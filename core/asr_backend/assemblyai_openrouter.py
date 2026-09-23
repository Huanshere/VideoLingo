import base64
import os
import time
import requests
from rich import print as rprint
from core.asr_backend.audio_preprocess import audio_slice_wav, get_audio_duration
from core.utils import *

# ------------
# OpenRouter Sync transcription limits
# ------------

DEFAULT_MODEL = "assemblyai/universal-3-5-pro"
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
MAX_SYNC_SECONDS = 120
DEFAULT_CHUNK_SECONDS = 110
DEFAULT_OVERLAP_SECONDS = 1.0
SPLIT_GAP = 1.0

# ------------
# language aliases
# ------------

LANG_ALIASES = {
    "english": "en",
    "chinese": "zh",
    "mandarin": "zh",
    "japanese": "ja",
    "french": "fr",
    "german": "de",
    "spanish": "es",
    "italian": "it",
    "russian": "ru",
    "korean": "ko",
}

ISO_639_2_TO_1 = {
    "eng": "en",
    "fra": "fr",
    "deu": "de",
    "ita": "it",
    "spa": "es",
    "rus": "ru",
    "kor": "ko",
    "jpn": "ja",
    "zho": "zh",
    "yue": "zh",
}

PLACEHOLDER_KEYS = {
    "YOUR_API_KEY",
    "YOUR_OPENROUTER_API_KEY",
    "your_elevenlabs_api_key",
}


# ------------
# config / auth
# ------------

def _usable_secret(value):
    if not isinstance(value, str):
        return False
    text = value.strip()
    if not text:
        return False
    if text in PLACEHOLDER_KEYS or text.lower().startswith("your_"):
        return False
    return True


def resolve_openrouter_key():
    configured = load_key_or("whisper.openrouter_api_key", "")
    if _usable_secret(configured):
        return configured.strip()
    env_key = os.environ.get("OPENROUTER_API_KEY", "")
    if _usable_secret(env_key):
        return env_key.strip()
    api_key = load_key_or("api.key", "")
    if _usable_secret(api_key):
        return api_key.strip()
    raise ValueError(
        "OpenRouter API key is not set. Set OPENROUTER_API_KEY, whisper.openrouter_api_key, or api.key."
    )


def resolve_openrouter_base_url():
    configured = load_key_or("whisper.openrouter_base_url", "")
    if isinstance(configured, str) and configured.strip():
        return configured.strip().rstrip("/")
    api_base = load_key_or("api.base_url", "")
    if isinstance(api_base, str) and "openrouter.ai" in api_base:
        return api_base.strip().rstrip("/")
    return DEFAULT_BASE_URL


def resolve_assemblyai_model():
    model = load_key_or("whisper.assemblyai_model", DEFAULT_MODEL)
    if isinstance(model, str) and model.strip():
        return model.strip()
    return DEFAULT_MODEL


# ------------
# chunk planning
# ------------

def plan_fixed_chunks(start, end, chunk_seconds=DEFAULT_CHUNK_SECONDS, overlap=DEFAULT_OVERLAP_SECONDS):
    """Plan overlapping windows that each stay within the Sync 120s limit."""
    if start is None:
        start = 0.0
    start = float(start)
    end = float(end)
    if end <= start:
        raise ValueError("Audio interval must have positive duration")
    duration = end - start
    if duration <= MAX_SYNC_SECONDS:
        return [(start, end)]

    chunk_seconds = float(chunk_seconds)
    overlap = float(overlap)
    if chunk_seconds > MAX_SYNC_SECONDS:
        chunk_seconds = MAX_SYNC_SECONDS
    if chunk_seconds <= 0:
        chunk_seconds = DEFAULT_CHUNK_SECONDS
    if overlap < 0:
        overlap = 0.0
    if overlap >= chunk_seconds:
        overlap = min(1.0, chunk_seconds / 10.0)
    step = chunk_seconds - overlap
    if step <= 0:
        step = chunk_seconds

    windows = []
    pos = start
    while pos < end - 1e-9:
        remaining = end - pos
        if remaining <= MAX_SYNC_SECONDS:
            windows.append((pos, end))
            break
        chunk_end = min(pos + chunk_seconds, end)
        windows.append((pos, chunk_end))
        pos += step
    return windows


def plan_chunks_for_file(audio_path, start, end):
    """Use silence near cut points when possible; otherwise fixed overlapping windows."""
    if start is None:
        start = 0.0
    if end is None:
        end = get_audio_duration(audio_path)
    windows = plan_fixed_chunks(start, end)
    if len(windows) <= 1:
        return windows
    try:
        refined = _snap_cuts_to_silence(audio_path, windows)
        if refined and all((ce - cs) <= MAX_SYNC_SECONDS + 1e-6 for cs, ce in refined):
            return refined
    except Exception as exc:
        rprint(f"[yellow]Silence-aware ASR split failed, using fixed chunks: {exc}[/yellow]")
    return windows


def _snap_cuts_to_silence(audio_path, windows, search_win=6.0):
    from pydub import AudioSegment
    from pydub.silence import detect_silence

    if len(windows) <= 1:
        return list(windows)
    audio = AudioSegment.from_file(audio_path)
    interval_end = windows[-1][1]
    cuts = [windows[0][0]]
    for index, (_cs, ce) in enumerate(windows[:-1]):
        threshold = ce
        ws = max(cuts[-1] + 1.0, threshold - search_win)
        we = min(interval_end, threshold + search_win)
        if we <= ws:
            cuts.append(threshold)
            continue
        regions = detect_silence(
            audio[int(ws * 1000):int(we * 1000)],
            min_silence_len=400,
            silence_thresh=-30,
        )
        snapped = None
        for silence_start, silence_end in regions:
            mid = ((silence_start + silence_end) / 2.0) / 1000.0 + ws
            if cuts[-1] < mid < interval_end and (mid - cuts[-1]) <= MAX_SYNC_SECONDS:
                snapped = mid
                break
        next_cut = snapped if snapped is not None else threshold
        if next_cut - cuts[-1] > MAX_SYNC_SECONDS:
            next_cut = cuts[-1] + MAX_SYNC_SECONDS
        cuts.append(next_cut)
    cuts.append(interval_end)
    refined = []
    for index in range(len(cuts) - 1):
        left, right = cuts[index], cuts[index + 1]
        if right - left <= 1e-6:
            continue
        if right - left <= MAX_SYNC_SECONDS:
            refined.append((left, right))
        else:
            refined.extend(plan_fixed_chunks(left, right))
    return refined or list(windows)


# ------------
# response parsing / stitching
# ------------

def _to_seconds(value, assume_ms):
    if value is None:
        return None
    number = float(value)
    if assume_ms:
        return number / 1000.0
    return number


def _looks_like_milliseconds(items):
    for item in items:
        for field in ("start", "end"):
            value = item.get(field)
            if value is not None and float(value) > 180:
                return True
    return False


def normalize_language(payload, fallback=None):
    code = payload.get("language") or payload.get("language_code") or fallback
    if not code or code == "auto":
        return fallback
    text = str(code).strip()
    mapped = LANG_ALIASES.get(text.lower()) or ISO_639_2_TO_1.get(text.lower())
    if mapped:
        return mapped
    if len(text) >= 2 and text[:2].isalpha():
        return text[:2].lower()
    return text


def extract_words(payload):
    """Accept OpenRouter verbose_json and AssemblyAI-native word lists."""
    raw = payload.get("words") or []
    if not raw:
        for segment in payload.get("segments") or []:
            raw.extend(segment.get("words") or [])
    if not raw:
        text = (payload.get("text") or "").strip()
        if not text:
            return []
        duration = payload.get("duration") or 0
        end = float(duration) if duration else 0.0
        return [{"word": text, "start": 0.0, "end": end}]

    assume_ms = _looks_like_milliseconds(raw)
    words = []
    for item in raw:
        token = item.get("word") or item.get("text") or ""
        token = str(token).strip()
        if not token:
            continue
        start = _to_seconds(item.get("start"), assume_ms)
        end = _to_seconds(item.get("end"), assume_ms)
        if start is None and end is None:
            continue
        if start is None:
            start = end
        if end is None:
            end = start
        if end < start:
            end = start
        word = {"word": token, "start": start, "end": end}
        speaker = item.get("speaker_id", item.get("speaker"))
        if speaker is not None:
            speaker_text = str(speaker)
            if not speaker_text.startswith("SPEAKER"):
                speaker_text = f"SPEAKER_{speaker_text}"
            word["speaker_id"] = speaker_text
        words.append(word)
    return words


def shift_words(words, offset):
    shifted = []
    for word in words:
        item = dict(word)
        item["start"] = word["start"] + offset
        item["end"] = word["end"] + offset
        shifted.append(item)
    return shifted


def stitch_word_lists(parts):
    """Keep later-chunk words only after the previous window's exclusive end."""
    merged = []
    for keep_from, words in parts:
        for word in words:
            if word["start"] < keep_from - 1e-6:
                continue
            merged.append(word)
    return merged


def words_to_whisper(words, language=None):
    """Match the segment/word shape used by WhisperX and ElevenLabs backends."""
    if not words:
        result = {"segments": []}
        if language:
            result["language"] = language
        return result

    segments = []
    current = None
    for item in words:
        if current is None:
            current = {
                "text": item["word"],
                "start": item["start"],
                "end": item["end"],
                "speaker_id": item.get("speaker_id"),
                "words": [{"word": item["word"], "start": item["start"], "end": item["end"]}],
            }
            continue
        gap = item["start"] - current["end"]
        speaker_changed = item.get("speaker_id") != current.get("speaker_id")
        if gap > SPLIT_GAP or speaker_changed:
            current["text"] = current["text"].strip()
            segments.append(current)
            current = {
                "text": item["word"],
                "start": item["start"],
                "end": item["end"],
                "speaker_id": item.get("speaker_id"),
                "words": [{"word": item["word"], "start": item["start"], "end": item["end"]}],
            }
            continue
        joiner = "" if current["text"].endswith((" ", "\n")) else " "
        current["text"] = (current["text"] + joiner + item["word"]).strip()
        current["end"] = item["end"]
        current["words"].append({"word": item["word"], "start": item["start"], "end": item["end"]})
    if current is not None:
        current["text"] = current["text"].strip()
        segments.append(current)
    result = {"segments": segments}
    if language:
        result["language"] = language
    return result


# ------------
# OpenRouter HTTP
# ------------

def build_transcription_payload(wav_bytes, language=None, model=None):
    payload = {
        "model": model or DEFAULT_MODEL,
        "input_audio": {
            "data": base64.b64encode(wav_bytes).decode("ascii"),
            "format": "wav",
        },
        "response_format": "verbose_json",
        "timestamp_granularities": ["word", "segment"],
        "provider": {
            "options": {
                "assemblyai": {"timestamps": True},
            }
        },
    }
    if language and language != "auto":
        payload["language"] = language
    return payload


def request_transcription(wav_bytes, language=None):
    api_key = resolve_openrouter_key()
    base_url = resolve_openrouter_base_url()
    model = resolve_assemblyai_model()
    url = f"{base_url}/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Huanshere/VideoLingo",
        "X-OpenRouter-Title": "VideoLingo",
    }
    payload = build_transcription_payload(wav_bytes, language=language, model=model)
    last_error = None
    for attempt in range(3):
        check_cancel()
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=180)
        except requests.RequestException as exc:
            last_error = exc
            rprint(f"[yellow]OpenRouter transcription request failed: {exc}, retry {attempt + 1}/3[/yellow]")
            time.sleep(2 ** attempt)
            continue
        if response.status_code in (429, 500, 502, 503, 504):
            last_error = RuntimeError(f"HTTP {response.status_code}: {response.text[:400]}")
            rprint(f"[yellow]OpenRouter transcription HTTP {response.status_code}, retry {attempt + 1}/3[/yellow]")
            time.sleep(2 ** attempt)
            continue
        if not response.ok:
            raise RuntimeError(
                f"OpenRouter transcription failed {response.status_code}: {response.text[:500]}"
            )
        data = response.json()
        if isinstance(data, dict) and data.get("error"):
            raise RuntimeError(f"OpenRouter transcription error: {data['error']}")
        return data
    raise RuntimeError(f"OpenRouter transcription failed after retries: {last_error}")


# ------------
# step 2 entry
# ------------

def transcribe_audio_assemblyai(raw_audio_path, vocal_audio_path, start=None, end=None):
    audio_path = vocal_audio_path or raw_audio_path
    rprint(f"[cyan]Transcribing with AssemblyAI Universal-3.5 Pro via OpenRouter: {audio_path}[/cyan]")
    if start is None:
        start = 0.0
    if end is None:
        end = get_audio_duration(audio_path)
    windows = plan_chunks_for_file(audio_path, start, end)
    rprint(
        f"[cyan]OpenRouter Sync limit is {MAX_SYNC_SECONDS}s; planned {len(windows)} chunk(s) "
        f"for {end - start:.1f}s audio[/cyan]"
    )

    language_hint = load_key_or("whisper.language", "auto")
    parts = []
    detected_language = None
    prev_end = None
    for index, (chunk_start, chunk_end) in enumerate(windows, start=1):
        check_cancel()
        chunk_len = chunk_end - chunk_start
        if chunk_len > MAX_SYNC_SECONDS + 1e-6:
            raise ValueError(
                f"Refusing OpenRouter Sync request of {chunk_len:.2f}s; max is {MAX_SYNC_SECONDS}s"
            )
        rprint(f"[cyan]Chunk {index}/{len(windows)}: {chunk_start:.2f}s -> {chunk_end:.2f}s ({chunk_len:.2f}s)[/cyan]")
        wav_bytes = audio_slice_wav(audio_path, chunk_start, chunk_end)
        payload = request_transcription(wav_bytes, language=language_hint)
        words = shift_words(extract_words(payload), chunk_start)
        detected_language = detected_language or normalize_language(payload)
        keep_from = chunk_start if prev_end is None else max(chunk_start, prev_end)
        parts.append((keep_from, words))
        prev_end = chunk_end

    merged = stitch_word_lists(parts)
    if language_hint and language_hint != "auto":
        language = language_hint
    else:
        language = detected_language
    if language:
        update_key("whisper.detected_language", language)
    parsed = words_to_whisper(merged, language=language)
    rprint(f"[green]AssemblyAI OpenRouter transcription produced {len(merged)} word(s)[/green]")
    return parsed
