"""ModelBest VoxCPM cloud TTS adapter for VideoLingo."""

import base64
import io
import json
import os
import tempfile
import wave
from pathlib import Path

import requests
from pydub import AudioSegment

from core.utils.config_utils import load_key_or
DEFAULT_BASE_URL = "https://api.modelbest.cn/v1"
MAX_REFERENCE_AUDIO_BYTES = 5 * 1024 * 1024
MAX_REFERENCE_AUDIO_DURATION_MS = 120_000
MAX_REFERENCE_UPLOAD_BYTES = 50 * 1024 * 1024
MAX_RESPONSE_AUDIO_BYTES = 100 * 1024 * 1024
NON_RETRYABLE_STATUS_CODES = {400, 401, 403, 404, 422}
VOXCPM_MODES = {"default", "clone", "high_fidelity"}
MANUAL_REFERENCE_AUDIO_PATH = Path("runtime/voxcpm/reference.wav")


class VoxCPMFatalError(ValueError):
    """A deterministic configuration or response error that must not be retried."""


def _finalize_streamed_wav(wav_audio: bytes) -> bytes:
    """Rewrite unknown streaming WAV lengths into valid file lengths."""
    if len(wav_audio) < 12 or wav_audio[:4] != b"RIFF" or wav_audio[8:12] != b"WAVE":
        raise ValueError("VoxCPM returned data that is not a RIFF/WAVE file")

    data_offset = None
    cursor = 12
    while cursor + 8 <= len(wav_audio):
        chunk_id = wav_audio[cursor : cursor + 4]
        chunk_size = int.from_bytes(wav_audio[cursor + 4 : cursor + 8], "little")
        chunk_data = cursor + 8
        if chunk_id == b"data":
            data_offset = chunk_data
            break
        cursor = chunk_data + chunk_size + (chunk_size & 1)

    if data_offset is None or data_offset > len(wav_audio):
        raise ValueError("VoxCPM returned a WAV without a data chunk")

    normalized = bytearray(wav_audio)
    normalized[4:8] = (len(normalized) - 8).to_bytes(4, "little")
    normalized[data_offset - 4 : data_offset] = (len(normalized) - data_offset).to_bytes(4, "little")
    return bytes(normalized)


def _iter_sse_events(response):
    """Yield JSON payloads from a Server-Sent Event response."""
    event_data = []
    for raw_line in response.iter_lines(decode_unicode=True):
        line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
        if not line:
            if event_data:
                try:
                    yield json.loads("\n".join(event_data))
                except (TypeError, ValueError) as exc:
                    raise VoxCPMFatalError("VoxCPM returned invalid SSE event data") from exc
                event_data = []
            continue
        if line.startswith("data:"):
            event_data.append(line.removeprefix("data:").strip())
    if event_data:
        try:
            yield json.loads("\n".join(event_data))
        except (TypeError, ValueError) as exc:
            raise VoxCPMFatalError("VoxCPM returned invalid trailing SSE event data") from exc


def _normalized_reference_wav(source) -> bytes:
    """Decode and normalize reference audio for ModelBest's bounded WAV input."""
    try:
        clip = AudioSegment.from_file(source)
    except Exception as exc:
        raise ValueError("failed to decode VoxCPM reference audio") from exc
    if len(clip) <= 0:
        raise ValueError("VoxCPM reference audio is empty")

    clip = clip[:MAX_REFERENCE_AUDIO_DURATION_MS]
    buffer = io.BytesIO()
    clip.set_channels(1).set_frame_rate(16000).export(
        buffer,
        format="wav",
        parameters=["-acodec", "pcm_s16le"],
    )
    wav_audio = buffer.getvalue()
    if not wav_audio or len(wav_audio) > MAX_REFERENCE_AUDIO_BYTES:
        raise ValueError("VoxCPM reference audio must be a non-empty WAV under 5 MiB")
    return wav_audio


def save_voxcpm_reference_audio(uploaded_audio: bytes) -> Path:
    """Validate and persist a manually uploaded reference clip as normalized WAV."""
    if not uploaded_audio:
        raise ValueError("VoxCPM reference audio is empty")
    if len(uploaded_audio) > MAX_REFERENCE_UPLOAD_BYTES:
        raise ValueError("VoxCPM reference upload exceeds 50 MiB")

    wav_audio = _normalized_reference_wav(io.BytesIO(uploaded_audio))
    output_path = MANUAL_REFERENCE_AUDIO_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(wav_audio)
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, output_path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return output_path


def _reference_audio_data_uri(reference_path: Path) -> str:
    """Normalize a VideoLingo reference clip for ModelBest's bounded WAV input."""
    wav_audio = _normalized_reference_wav(reference_path)
    encoded = base64.b64encode(wav_audio).decode("ascii")
    return f"data:audio/wav;base64,{encoded}"


def _resolve_mode(settings: dict) -> str:
    """Resolve the current mode, including compatibility with the old boolean setting."""
    mode = settings.get("mode")
    if mode in VOXCPM_MODES:
        return mode
    legacy_high_fidelity = settings.get("high_fidelity")
    if legacy_high_fidelity is True:
        return "high_fidelity"
    if legacy_high_fidelity is False:
        return "default"
    return "clone"


def _get_reference_audio(number: int) -> tuple[Path, int]:
    current_dir = Path.cwd()
    reference_path = current_dir / "output" / "audio" / "refers" / f"{number}.wav"
    reference_number = number
    if not reference_path.exists():
        from core._9_refer_audio import extract_refer_audio_main

        extract_refer_audio_main()
    if not reference_path.exists():
        reference_path = current_dir / "output" / "audio" / "refers" / "1.wav"
        reference_number = 1
    if not reference_path.exists():
        raise FileNotFoundError(f"VoxCPM reference audio was not created: {reference_path}")

    return reference_path, reference_number


def _get_reference_context(number: int, task_df) -> tuple[Path, str]:
    reference_path, reference_number = _get_reference_audio(number)

    row = task_df.loc[task_df["number"] == reference_number, "origin"]
    prompt_value = row.iloc[0] if not row.empty else None
    prompt_text = prompt_value.strip() if isinstance(prompt_value, str) else ""
    if not prompt_text:
        raise ValueError(f"VoxCPM needs source transcript text for segment {reference_number}")
    return reference_path, prompt_text


def _get_manual_reference_context(settings: dict) -> tuple[Path, str] | None:
    """Return the user-supplied reference and its exact transcript when present."""
    if not MANUAL_REFERENCE_AUDIO_PATH.exists():
        return None
    prompt_value = settings.get("prompt_text", "")
    prompt_text = prompt_value.strip() if isinstance(prompt_value, str) else ""
    return MANUAL_REFERENCE_AUDIO_PATH, prompt_text


def voxcpm_tts_for_videolingo(text: str, save_as: str, number: int, task_df) -> bool:
    """Generate a WAV through ModelBest's streaming VoxCPM Audio Speech API."""
    settings = load_key_or("voxcpm", {})
    api_key = str(settings.get("api_key", "") or "").strip()
    model_id = str(settings.get("model_id", "") or "").strip()
    if not api_key:
        raise VoxCPMFatalError("VoxCPM API key is not configured")
    if not model_id:
        raise VoxCPMFatalError("VoxCPM model ID is not configured")

    base_url = str(settings.get("base_url", DEFAULT_BASE_URL) or DEFAULT_BASE_URL).strip().rstrip("/")
    payload = {
        "model": model_id,
        "input": text,
        # ModelBest does not currently expose a VoxCPM voice catalog. The
        # OpenAI-compatible schema still requires this protocol placeholder;
        # speaker identity comes from ref_audio / prompt_audio when cloning.
        "voice": "default",
        "response_format": "wav",
        "stream": True,
    }

    mode = _resolve_mode(settings)
    if mode != "default":
        try:
            manual_reference = _get_manual_reference_context(settings)
            if manual_reference is not None:
                reference_path, prompt_text = manual_reference
                if mode == "high_fidelity" and not prompt_text:
                    raise ValueError(
                        "VoxCPM high-fidelity cloning needs the exact transcript of the uploaded reference audio"
                    )
            elif mode == "high_fidelity":
                reference_path, prompt_text = _get_reference_context(number, task_df)
            else:
                reference_path, _ = _get_reference_audio(number)
                prompt_text = ""
            reference_audio = _reference_audio_data_uri(reference_path)
        except (FileNotFoundError, ValueError, TypeError, AttributeError) as exc:
            raise VoxCPMFatalError(str(exc)) from exc
        payload["ref_audio"] = reference_audio
        if mode == "high_fidelity":
            payload["prompt_audio"] = reference_audio
            payload["prompt_text"] = prompt_text

    response = requests.post(
        f"{base_url}/audio/speech",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
        json=payload,
        stream=True,
        timeout=(10, 120),
    )
    try:
        if response.status_code != 200:
            message = f"VoxCPM request failed with HTTP {response.status_code}: {response.text[:500]}"
            if response.status_code in NON_RETRYABLE_STATUS_CODES:
                raise VoxCPMFatalError(message)
            raise requests.HTTPError(message, response=response)

        chunks = []
        total_audio_bytes = 0
        completed = False
        for event in _iter_sse_events(response):
            event_type = event.get("type")
            if event_type == "error":
                raise VoxCPMFatalError(str(event.get("error") or "VoxCPM returned an error event"))
            if event_type == "speech.audio.delta":
                encoded_audio = event.get("audio")
                if not isinstance(encoded_audio, str) or not encoded_audio:
                    raise VoxCPMFatalError("VoxCPM returned an empty audio chunk")
                try:
                    decoded_audio = base64.b64decode(encoded_audio, validate=True)
                except (TypeError, ValueError) as exc:
                    raise VoxCPMFatalError("VoxCPM returned invalid Base64 audio") from exc
                total_audio_bytes += len(decoded_audio)
                if total_audio_bytes > MAX_RESPONSE_AUDIO_BYTES:
                    raise VoxCPMFatalError("VoxCPM audio response exceeds 100 MiB")
                chunks.append(decoded_audio)
            elif event_type == "speech.audio.done":
                completed = True
                break
        if not completed:
            raise VoxCPMFatalError("VoxCPM stream ended before speech.audio.done")
        wav_audio = b"".join(chunks)
        if not wav_audio:
            raise VoxCPMFatalError("VoxCPM returned no audio")
        try:
            wav_audio = _finalize_streamed_wav(wav_audio)
        except ValueError as exc:
            raise VoxCPMFatalError(str(exc)) from exc

        try:
            with wave.open(io.BytesIO(wav_audio), "rb") as wav_file:
                if wav_file.getnframes() <= 0 or wav_file.getframerate() <= 0:
                    raise VoxCPMFatalError("VoxCPM returned an empty WAV")
        except wave.Error as exc:
            raise VoxCPMFatalError("VoxCPM returned an invalid WAV") from exc

        output_path = Path(save_as)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                dir=output_path.parent,
                prefix=f".{output_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary.write(wav_audio)
                temporary_path = Path(temporary.name)
            os.replace(temporary_path, output_path)
            temporary_path = None
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
        return True
    finally:
        response.close()
