"""Local Qwen3-ASR + Qwen3-ForcedAligner backend (default local ASR).

Dual track, like the WhisperX path: Qwen3-ASR transcribes the raw audio, then
Qwen3-ForcedAligner aligns that text against the vocal track (raw audio when
Demucs is off). The result uses WhisperX's segment/word structure so
process_transcription, the ASR cache and dubbing are unchanged.

Engines:
- mlx: Apple Silicon via mlx-audio (8-bit mlx-community weights).
- transformers: Windows / Linux / other Macs via the official qwen-asr package.
Heavy libraries are imported lazily so this module imports without them.
"""

import gc
import importlib.util
import platform
import subprocess
import time
import unicodedata
from collections import Counter
from pathlib import Path

import numpy as np
from rich import print as rprint
from core.utils import load_key, load_key_or, except_handler, check_cancel

SAMPLE_RATE = 16000
# Qwen3-ForcedAligner accepts at most 180 s per call (qwen_asr MAX_FORCE_ALIGN_INPUT_SECONDS).
# ASR uses the same windows so each transcript aligns against exactly its own audio.
WINDOW_SECONDS = 180
# Cut each window at the quietest 100 ms inside its last 30 s.
CUT_SEARCH_SECONDS = 30
MAX_NEW_TOKENS = 2048
MAX_WORD_LENGTH = 30  # process_transcription drops longer words

MODELS = {
    "mlx": {
        "1.7b": "mlx-community/Qwen3-ASR-1.7B-8bit",
        "0.6b": "mlx-community/Qwen3-ASR-0.6B-8bit",
        "aligner": "mlx-community/Qwen3-ForcedAligner-0.6B-8bit",
    },
    "transformers": {
        "1.7b": "Qwen/Qwen3-ASR-1.7B",
        "0.6b": "Qwen/Qwen3-ASR-0.6B",
        "aligner": "Qwen/Qwen3-ForcedAligner-0.6B",
    },
}

# ISO 639-1 (whisper.language / detected_language) <-> Qwen3-ASR language names.
ISO_TO_QWEN = {
    "zh": "Chinese", "en": "English", "yue": "Cantonese", "ar": "Arabic", "de": "German",
    "fr": "French", "es": "Spanish", "pt": "Portuguese", "id": "Indonesian", "it": "Italian",
    "ko": "Korean", "ru": "Russian", "th": "Thai", "vi": "Vietnamese", "ja": "Japanese",
    "tr": "Turkish", "hi": "Hindi", "ms": "Malay", "nl": "Dutch", "sv": "Swedish",
    "da": "Danish", "fi": "Finnish", "pl": "Polish", "cs": "Czech", "fil": "Filipino",
    "fa": "Persian", "el": "Greek", "ro": "Romanian", "hu": "Hungarian", "mk": "Macedonian",
}
QWEN_TO_ISO = {name: code for code, name in ISO_TO_QWEN.items()}
# Downstream splitting/joining only knows "zh"; Cantonese is written in Chinese characters.
QWEN_TO_ISO["Cantonese"] = "zh"


# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

def _apple_silicon():
    return platform.system() == "Darwin" and platform.machine() == "arm64"


def _installed(module):
    return importlib.util.find_spec(module) is not None


def model_size(requested=None):
    size = str(requested or load_key_or("whisper.qwen_model", "1.7b")).lower()
    if size not in ("1.7b", "0.6b"):
        raise ValueError(f"whisper.qwen_model must be '1.7b' or '0.6b', got {size!r}")
    return size


def resolve_engine(requested=None):
    """auto -> MLX on Apple Silicon when mlx-audio is installed, else the qwen-asr transformers backend."""
    engine = str(requested or load_key_or("whisper.qwen_engine", "auto")).lower()
    if engine not in ("auto", "mlx", "transformers"):
        raise ValueError(f"whisper.qwen_engine must be 'auto', 'mlx' or 'transformers', got {engine!r}")
    if engine == "auto":
        engine = "mlx" if _apple_silicon() and _installed("mlx_audio") else "transformers"
    module = "mlx_audio" if engine == "mlx" else "qwen_asr"
    if not _installed(module):
        package = "mlx-audio" if engine == "mlx" else "qwen-asr"
        raise ImportError(
            f"Qwen ASR engine '{engine}' needs the '{package}' package. Rerun `python installer.py`, "
            "or install the optional WhisperX fallback (docs/pages/docs/whisperx-optional.en-US.md) "
            "and set whisper.backend: whisperx."
        )
    return engine


def _model_source(repo_id):
    """Prefer a complete local copy in model_dir (e.g. _model_cache/Qwen3-ASR-1.7B); else the HF cache/Hub."""
    local = Path(load_key("model_dir")) / repo_id.split("/")[-1]
    if (local / "config.json").is_file():
        rprint(f"[green]Using local Qwen model: {local.resolve()}[/green]")
        return str(local.resolve())
    return repo_id


def qwen_language(language):
    """Map whisper.language to a Qwen language name; None lets Qwen detect it."""
    if not language or language == "auto":
        return None
    if language not in ISO_TO_QWEN:
        raise ValueError(f"Qwen3-ASR does not support language '{language}'. Supported: {sorted(ISO_TO_QWEN)}")
    return ISO_TO_QWEN[language]


def iso_language(name):
    """Qwen may report 'Chinese,English' for code-switched audio; the first language is primary."""
    first = (name or "").split(",")[0].strip()
    first = first[:1].upper() + first[1:].lower()
    return QWEN_TO_ISO.get(first)


# ------------------------------------------------------------------
# Audio
# ------------------------------------------------------------------

def load_audio_segment(path, start, end):
    """Decode [start, end) to 16 kHz mono float32 with the FFmpeg CLI.

    librosa.load deadlocks inside Streamlit's ScriptRunner thread (see whisperX_local).
    """
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-ss", str(start), "-i", str(path),
           "-t", str(end - start), "-ac", "1", "-ar", str(SAMPLE_RATE), "-f", "f32le", "pipe:1"]
    data = subprocess.run(cmd, check=True, capture_output=True).stdout
    return np.frombuffer(data, dtype=np.float32).copy()


def split_windows(wav, sr=SAMPLE_RATE, window_seconds=WINDOW_SECONDS, search_seconds=CUT_SEARCH_SECONDS):
    """Split samples into contiguous (start, end) windows of at most window_seconds, cut at low energy."""
    total, max_len = len(wav), int(window_seconds * sr)
    search, frame = int(search_seconds * sr), max(1, int(0.1 * sr))
    windows, start = [], 0
    while total - start > max_len:
        right = start + max_len
        left = max(start + 1, right - search)
        energy = np.convolve(np.abs(wav[left:right]), np.ones(frame, dtype=np.float32), mode="valid")
        cut = left + int(np.argmin(energy)) + frame // 2 if len(energy) else right
        windows.append((start, cut))
        start = cut
    windows.append((start, total))
    return windows


# ------------------------------------------------------------------
# Words: restore punctuation that the aligner strips
# ------------------------------------------------------------------

def _is_token_char(ch):
    # Qwen3ForceAlignProcessor keeps letters, numbers and apostrophes only.
    return ch == "'" or unicodedata.category(ch)[0] in "LN"


def attach_words(text, items, offset=0.0):
    """Map aligner tokens back onto the ASR text so words keep punctuation.

    Aligner tokens are ordered subsequences of the text with punctuation removed
    ("U.S.," -> "US"); each word takes its token's span plus adjacent punctuation,
    e.g. "Hello, world." -> ["Hello,", "world."], "你好，世界。" -> ["你", "好，", "世", "界。"].
    """
    words, pos, n = [], 0, len(text)
    for token, start, end in items:
        if not token:
            continue
        j = pos
        for ch in token:
            while j < n and text[j] != ch:
                j += 1
            if j >= n:
                break
            j += 1
        else:
            while j < n and not text[j].isspace() and not _is_token_char(text[j]):
                j += 1
            surface = text[pos:j].strip()
            pos = j
            if len(surface) > MAX_WORD_LENGTH:
                surface = token
            start, end = max(0.0, float(start)), max(0.0, float(end))
            words.append({"word": surface, "start": round(offset + start, 3),
                          "end": round(offset + max(start, end), 3)})
            continue
        # Token not found in order (should not happen); keep its bare text without consuming the transcript.
        start, end = max(0.0, float(start)), max(0.0, float(end))
        words.append({"word": token, "start": round(offset + start, 3), "end": round(offset + max(start, end), 3)})
    if words and pos < n:
        # Trailing punctuation left after the last token (e.g. closing quotes).
        tail = text[pos:].strip()
        if tail and len(words[-1]["word"] + tail) <= MAX_WORD_LENGTH:
            words[-1]["word"] += tail
    return words


# ------------------------------------------------------------------
# Engines
# ------------------------------------------------------------------

def _free(engine):
    gc.collect()
    if engine == "mlx":
        import mlx.core as mx
        mx.clear_cache()
    else:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


def _torch_device():
    import torch
    if torch.cuda.is_available():
        dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        return "cuda:0", dtype
    return "cpu", torch.float32


def _transcribe(engine, repo_id, clips, language):
    """Return [(qwen_language_name, text)] per clip."""
    source = _model_source(repo_id)
    if engine == "mlx":
        from mlx_audio.stt.utils import load_model
        model = load_model(source)
        outputs = []
        for clip in clips:
            check_cancel()
            out = model.generate(clip, language=language, max_tokens=MAX_NEW_TOKENS,
                                 chunk_duration=WINDOW_SECONDS + 1)
            detected = language or ",".join(dict.fromkeys(l for l in (out.language or []) if l))
            outputs.append((detected, out.text.strip()))
    else:
        from qwen_asr import Qwen3ASRModel
        device, dtype = _torch_device()
        rprint(f"[cyan]🎮 Qwen3-ASR device:[/cyan] {device}, [cyan]dtype:[/cyan] {dtype}")
        model = Qwen3ASRModel.from_pretrained(source, dtype=dtype, device_map=device,
                                              max_inference_batch_size=1, max_new_tokens=MAX_NEW_TOKENS)
        outputs = []
        for clip in clips:
            check_cancel()
            out = model.transcribe(audio=(clip, SAMPLE_RATE), language=language)[0]
            outputs.append((language or out.language, out.text.strip()))
    del model
    _free(engine)
    return outputs


def _align(engine, repo_id, jobs):
    """jobs: [(clip, text, qwen_language)] -> [[(token, start, end)]] relative to each clip."""
    source = _model_source(repo_id)
    if engine == "mlx":
        from mlx_audio.stt.utils import load_model
        aligner = load_model(source)
        align = lambda clip, text, lang: aligner.generate(clip, text=text, language=lang)
    else:
        from qwen_asr import Qwen3ForcedAligner
        device, dtype = _torch_device()
        aligner = Qwen3ForcedAligner.from_pretrained(source, dtype=dtype, device_map=device)
        align = lambda clip, text, lang: aligner.align(audio=(clip, SAMPLE_RATE), text=text, language=lang)[0]
    results = []
    for clip, text, lang in jobs:
        check_cancel()
        result = align(clip, text, lang)
        results.append([(item.text, item.start_time, item.end_time) for item in result])
    del aligner, align
    _free(engine)
    return results


# ------------------------------------------------------------------
# Entry point (same signature as whisperX_local.transcribe_audio)
# ------------------------------------------------------------------

@except_handler("Qwen ASR processing error:")
def transcribe_audio(raw_audio_file, vocal_audio_file, start, end):
    engine = resolve_engine()
    size = model_size()
    models = MODELS[engine]
    configured = load_key("whisper.language")
    forced = qwen_language(configured)
    rprint(f"[green]▶️ Qwen3-ASR {size} + ForcedAligner ({engine}) for segment {start:.2f}s to {end:.2f}s...[/green]")

    raw = load_audio_segment(raw_audio_file, start, end)
    vocal = raw if vocal_audio_file == raw_audio_file else load_audio_segment(vocal_audio_file, start, end)
    # Drop slivers (< 0.1 s) left by segment boundaries; they carry no speech.
    windows = [(a, b) for a, b in split_windows(raw) if b - a >= SAMPLE_RATE // 10]

    # 1. transcribe raw audio
    t0 = time.time()
    texts = _transcribe(engine, models[size], [raw[a:b] for a, b in windows], forced)
    rprint(f"[cyan]⏱️ time transcribe:[/cyan] {time.time() - t0:.2f}s")

    if forced:
        detected = configured
    else:
        votes = Counter(iso_language(lang) for lang, text in texts if text and iso_language(lang))
        detected = votes.most_common(1)[0][0] if votes else None
        if not detected and any(text for _, text in texts):
            raise ValueError("Qwen3-ASR could not detect the language; set the recognition language and retry.")

    # 2. align by vocal audio
    t0 = time.time()
    todo = [(i, lang or ISO_TO_QWEN[detected]) for i, (lang, text) in enumerate(texts) if text]
    jobs = [(vocal[windows[i][0]:windows[i][1]], texts[i][1], lang.split(",")[0]) for i, lang in todo]
    aligned = _align(engine, models["aligner"], jobs) if jobs else []
    rprint(f"[cyan]⏱️ time align:[/cyan] {time.time() - t0:.2f}s")

    segments = []
    for (i, _), items in zip(todo, aligned):
        offset = start + windows[i][0] / SAMPLE_RATE
        words = attach_words(texts[i][1], items, offset)
        if words:
            segments.append({"text": texts[i][1], "start": words[0]["start"],
                             "end": words[-1]["end"], "words": words})
    return {"language": detected, "segments": segments}
