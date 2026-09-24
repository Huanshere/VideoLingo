from __future__ import annotations

import importlib
import re
import subprocess
import threading
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from rich import print as rprint

from core.utils.config_utils import load_key, update_key

DEFAULT_MODEL = "iic/SenseVoiceSmall"
SUPPORTED_LANGUAGES = frozenset({"zh", "en", "ja"})
SUPPORTED_DEVICES = frozenset({"auto", "cpu", "cuda"})

_RICH_TAG_PATTERN = re.compile(r"<\|[^|]*\|>")
_TOKEN_PATTERN = re.compile(
    r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]"
    r"|[A-Za-z0-9]+(?:['’][A-Za-z0-9]+)?"
    r"|[^\s]"
)
_NO_SPACE_BEFORE = frozenset(".,!?;:%)]}，。！？；：、…'’")
_NO_SPACE_AFTER = frozenset("([{'‘“")
_MAX_WORD_CHARS = 30

_MODEL_CACHE: dict[tuple[str, str], Any] = {}
_INFERENCE_LOCKS: dict[tuple[str, str], threading.Lock] = {}
_MODEL_CACHE_LOCK = threading.Lock()


def clear_model_cache() -> None:
    with _MODEL_CACHE_LOCK:
        _MODEL_CACHE.clear()
        _INFERENCE_LOCKS.clear()


def resolve_device(device: str) -> str:
    if device not in SUPPORTED_DEVICES:
        choices = ", ".join(sorted(SUPPORTED_DEVICES))
        raise ValueError(
            f"Unsupported FunASR device '{device}'. Choose one of: {choices}."
        )
    if device != "auto":
        return device

    torch = importlib.import_module("torch")
    return "cuda" if torch.cuda.is_available() else "cpu"


def create_model(model_name: str, device: str):
    try:
        auto_model = importlib.import_module("funasr").AutoModel
    except ImportError as exc:
        raise RuntimeError(
            "FunASR is an optional VideoLingo backend. Install it with "
            "`python installer.py --with-funasr`, then restart VideoLingo."
        ) from exc

    return auto_model(
        model=model_name,
        vad_model="fsmn-vad",
        vad_kwargs={"max_single_segment_time": 30_000},
        device=device,
        disable_update=True,
        disable_pbar=True,
    )


def get_model(model_name: str, device: str):
    cache_key = (model_name, device)
    with _MODEL_CACHE_LOCK:
        if cache_key not in _MODEL_CACHE:
            rprint(f"[cyan]Loading FunASR model {model_name} on {device}...[/cyan]")
            _MODEL_CACHE[cache_key] = create_model(model_name, device)
        _INFERENCE_LOCKS.setdefault(cache_key, threading.Lock())
        return _MODEL_CACHE[cache_key]


def get_inference_lock(model_name: str, device: str) -> threading.Lock:
    cache_key = (model_name, device)
    with _MODEL_CACHE_LOCK:
        return _INFERENCE_LOCKS.setdefault(cache_key, threading.Lock())


def clean_text(text: str) -> str:
    try:
        postprocess = importlib.import_module("funasr.utils.postprocess_utils")
    except ImportError:
        return _RICH_TAG_PATTERN.sub("", text or "").strip()
    return postprocess.rich_transcription_postprocess(text or "").strip()


def _timestamp_pair_ms(timestamp: Any) -> tuple[int, int] | None:
    if isinstance(timestamp, dict):
        start = timestamp.get("start_time", timestamp.get("start"))
        end = timestamp.get("end_time", timestamp.get("end"))
        if start is None or end is None:
            return None
        start_ms = int(float(start) * 1000)
        end_ms = int(float(end) * 1000)
    elif isinstance(timestamp, (list, tuple)) and len(timestamp) >= 2:
        start_ms = int(timestamp[0])
        end_ms = int(timestamp[1])
    else:
        return None

    if start_ms < 0 or end_ms <= start_ms:
        return None
    return start_ms, end_ms


def _split_overlong_words(words: list[dict]) -> list[dict]:
    split_words = []
    for word in words:
        text = word["word"]
        if len(text) <= _MAX_WORD_CHARS:
            split_words.append(word)
            continue

        start = word["start"]
        end = word["end"]
        duration = end - start
        for chunk_start in range(0, len(text), _MAX_WORD_CHARS):
            chunk_end = min(chunk_start + _MAX_WORD_CHARS, len(text))
            chunk = word.copy()
            chunk["word"] = text[chunk_start:chunk_end]
            chunk["start"] = start + duration * chunk_start / len(text)
            chunk["end"] = (
                end
                if chunk_end == len(text)
                else start + duration * chunk_end / len(text)
            )
            split_words.append(chunk)
    return split_words


def aligned_words(result: dict, offset_seconds: float) -> list[dict]:
    words = result.get("words") or []
    timestamps = result.get("timestamp") or result.get("timestamps") or []
    if not words or len(words) != len(timestamps):
        return []

    aligned = []
    for word, timestamp in zip(words, timestamps):
        pair = _timestamp_pair_ms(timestamp)
        text = _RICH_TAG_PATTERN.sub("", str(word)).strip()
        if pair is None or not text:
            return []
        aligned.append(
            {
                "word": text,
                "start": offset_seconds + pair[0] / 1000,
                "end": offset_seconds + pair[1] / 1000,
            }
        )
    return _split_overlong_words(aligned)


def _timestamp_bounds_seconds(
    result: dict,
    offset_seconds: float,
    clip_duration_seconds: float,
) -> tuple[float, float]:
    timestamps = result.get("timestamp") or result.get("timestamps") or []
    pairs = [_timestamp_pair_ms(timestamp) for timestamp in timestamps]
    valid = [pair for pair in pairs if pair is not None]
    if valid:
        return (
            offset_seconds + min(pair[0] for pair in valid) / 1000,
            offset_seconds + max(pair[1] for pair in valid) / 1000,
        )
    return offset_seconds, offset_seconds + clip_duration_seconds


def fallback_words(
    result: dict,
    offset_seconds: float,
    clip_duration_seconds: float,
) -> list[dict]:
    tokens = _TOKEN_PATTERN.findall(clean_text(result.get("text", "")))
    if not tokens:
        return []

    start, end = _timestamp_bounds_seconds(
        result, offset_seconds, clip_duration_seconds
    )
    if end <= start:
        end = start + max(0.001, clip_duration_seconds)
    step = (end - start) / len(tokens)
    words = []
    for index, token in enumerate(tokens):
        token_start = start + index * step
        token_end = end if index == len(tokens) - 1 else start + (index + 1) * step
        words.append({"word": token, "start": token_start, "end": token_end})
    return _split_overlong_words(words)


def _is_cjk(char: str) -> bool:
    codepoint = ord(char)
    return any(
        start <= codepoint <= end
        for start, end in (
            (0x3040, 0x30FF),
            (0x3400, 0x4DBF),
            (0x4E00, 0x9FFF),
            (0xAC00, 0xD7AF),
        )
    )


def join_words(words: list[str]) -> str:
    text = ""
    for word in words:
        if not text:
            text = word
        elif (
            word[0] in _NO_SPACE_BEFORE
            or text[-1] in _NO_SPACE_AFTER
            or (_is_cjk(text[-1]) and _is_cjk(word[0]))
        ):
            text += word
        else:
            text += f" {word}"
    return text.strip()


def extract_audio_segment(
    audio_file: str,
    output_file: str | Path,
    start: float,
    end: float,
) -> None:
    duration = end - start
    if duration <= 0:
        raise ValueError(f"Invalid audio segment: start={start}, end={end}")

    command = [
        "ffmpeg",
        "-nostdin",
        "-loglevel",
        "error",
        "-y",
        "-ss",
        f"{start:.3f}",
        "-t",
        f"{duration:.3f}",
        "-i",
        audio_file,
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(output_file),
    ]
    subprocess.run(
        command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
    )


def _segments_from_results(
    results: list[dict],
    offset_seconds: float,
    clip_duration_seconds: float,
) -> list[dict]:
    segments = []
    for result in results:
        words = aligned_words(result, offset_seconds)
        if not words:
            words = fallback_words(result, offset_seconds, clip_duration_seconds)
        if not words:
            continue

        text = clean_text(result.get("text", ""))
        if not text:
            text = join_words([word["word"] for word in words])
        segments.append(
            {
                "start": words[0]["start"],
                "end": words[-1]["end"],
                "text": text,
                "words": words,
            }
        )
    return segments


def transcribe_audio(
    raw_audio_file: str,
    vocal_audio_file: str,
    start: float,
    end: float,
) -> dict:
    model_name = load_key("funasr.model") or DEFAULT_MODEL
    configured_device = load_key("funasr.device") or "auto"
    language = load_key("whisper.language")
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            "The VideoLingo FunASR/SenseVoice backend currently supports zh, en, and ja. "
            f"The configured recognition language is '{language}'."
        )

    device = resolve_device(configured_device)
    model = get_model(model_name, device)
    source_audio = vocal_audio_file or raw_audio_file
    clip_duration = float(end) - float(start)
    rprint(
        f"[cyan]Transcribing {start:.2f}s-{end:.2f}s with "
        f"FunASR model {model_name} on {device}...[/cyan]"
    )

    with TemporaryDirectory(prefix="videolingo-funasr-") as temp_dir:
        segment_path = Path(temp_dir) / "segment.wav"
        extract_audio_segment(source_audio, segment_path, float(start), float(end))
        with get_inference_lock(model_name, device):
            results = model.generate(
                input=str(segment_path),
                cache={},
                language=language,
                use_itn=True,
                batch_size_s=60,
                merge_vad=True,
                merge_length_s=15,
                output_timestamp=True,
                return_time_stamps=True,
            )

    update_key("whisper.detected_language", language)
    segments = _segments_from_results(results or [], float(start), clip_duration)
    if not segments:
        raise RuntimeError("FunASR returned no timestamped transcription segments.")
    return {"segments": segments, "language": language}


__all__ = [
    "DEFAULT_MODEL",
    "SUPPORTED_LANGUAGES",
    "aligned_words",
    "clean_text",
    "clear_model_cache",
    "create_model",
    "extract_audio_segment",
    "fallback_words",
    "get_inference_lock",
    "get_model",
    "join_words",
    "resolve_device",
    "transcribe_audio",
]
