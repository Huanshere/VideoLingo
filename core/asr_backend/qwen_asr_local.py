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
import math
import platform
import re
import subprocess
import time
import unicodedata
from collections import Counter
from contextlib import contextmanager
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
MAX_NEW_TOKENS = 2400
# Token budget by clip length, so a looping clip stops early instead of generating a fixed
# maximum. Transcripts: the fastest Chinese/Japanese speech (~8 chars/s, most common
# characters one token, plus punctuation) needs ~6-8 tokens/s, English far less; 13/s is
# 1.6x that, and a 180 s window gets 2372 tokens (the old flat cap was 2048).
TOKENS_PER_SECOND = 13
TOKEN_MARGIN = 32
# Probes only decide the language and give a size reference, so they get a tighter budget:
# 20 s -> 116 tokens (~100-150 CJK chars or ~90 English words). A cut probe only lowers the
# reference used by the checks below, which makes them more lenient, never stricter.
# A looping 20 s probe took 11.1 s at 2048 tokens and 5.7 s at 252 on an M4 (~2.8 s normal).
PROBE_TOKENS_PER_SECOND = 5
PROBE_TOKEN_MARGIN = 16
# Shorter windows are dropped; MLX would otherwise zero-pad anything under its 1 s default.
MIN_WINDOW_SECONDS = 0.1

# Language detection with whisper.language = auto. Detecting on a whole window let one
# misleading stretch decide it: 1.7B heard a Chinese/English code-switched opening as
# English and looped "Yeah, yeah." for 120 s. Probe short clips spread over the window,
# vote, then transcribe the window with that language forced.
PROBE_SECONDS = 20
PROBES_PER_WINDOW = 3

# Degenerate output: a phrase repeated back to back over at least half of a transcript of
# REPEAT_MIN_CHARS+ letters/digits, or a window transcript shorter than half of what its
# probes (same language) heard. Retry once in RETRY_WINDOW_SECONDS windows, then fail.
REPEAT_MIN_CHARS = 40
REPEAT_COVERAGE = 0.5
PROBE_MIN_CHARS = 30
PROBE_COVERAGE = 0.5
RETRY_WINDOW_SECONDS = 60
RETRY_SEARCH_SECONDS = 15
# Without same-language probes (forced language, or a window voted into another language),
# a transcript under SPARSE_CHARS_PER_SECOND triggers auto-language probes of the window;
# it is degenerate if it has under CROSS_LANGUAGE_COVERAGE of what they heard in any
# language. Normal speech is 4+ chars/s (Chinese) to 10+ letters/s (English), so this costs
# nothing on normal windows; silence/music probes hear nothing and are never flagged.
SPARSE_CHARS_PER_SECOND = 2.0
CROSS_LANGUAGE_COVERAGE = 0.25
# auto: if every probe of the segment looped, probe again with more, shorter clips.
REPROBE_SECONDS = 10
REPROBES_PER_WINDOW = 6
_REPEATED_UNIT = re.compile(r"(.{1,40}?)\1{3,}", re.S)
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
    """auto -> MLX on Apple Silicon (qwen-asr only if it is what this environment has), else transformers."""
    engine = str(requested or load_key_or("whisper.qwen_engine", "auto")).lower()
    if engine not in ("auto", "mlx", "transformers"):
        raise ValueError(f"whisper.qwen_engine must be 'auto', 'mlx' or 'transformers', got {engine!r}")
    if engine == "auto":
        # Apple Silicon requirements install mlx-audio, not qwen-asr; point a broken install back to it.
        mlx = _apple_silicon() and (_installed("mlx_audio") or not _installed("qwen_asr"))
        engine = "mlx" if mlx else "transformers"
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


def primary_language(name):
    """Qwen may report 'Chinese,English' for code-switched audio; the first language is primary.

    Returns the supported Qwen language name, or None.
    """
    first = (name or "").split(",")[0].strip()
    first = first[:1].upper() + first[1:].lower()
    return first if first in QWEN_TO_ISO else None


def iso_language(name):
    return QWEN_TO_ISO.get(primary_language(name))


# ------------------------------------------------------------------
# Audio
# ------------------------------------------------------------------

def load_audio_segment(path, start, end):
    """Decode [start, end) to 16 kHz mono float32 with the FFmpeg CLI.

    librosa.load deadlocks inside Streamlit's ScriptRunner thread (see whisperX_local).
    """
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-ss", str(start), "-i", str(path),
           "-t", str(end - start), "-ac", "1", "-ar", str(SAMPLE_RATE), "-f", "f32le", "pipe:1"]
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode:
        stderr = proc.stderr.decode("utf-8", "replace").strip()
        raise RuntimeError(f"FFmpeg could not decode {path} ({start}-{end}s): {stderr or f'exit code {proc.returncode}'}")
    return np.frombuffer(proc.stdout, dtype=np.float32).copy()


def match_length(wav, length):
    """Trim or zero-pad so the vocal track shares the raw track's sample indices.

    demucs_vl writes stems that start sample-aligned with raw.mp3 (FFmpeg decode and
    encode, so MP3 encoder delay is trimmed); only the decoded tail length can differ.
    """
    if len(wav) >= length:
        return wav[:length]
    return np.concatenate([wav, np.zeros(length - len(wav), dtype=wav.dtype)])


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
# Language probes and degenerate output
# ------------------------------------------------------------------

def probe_ranges(length, sr=SAMPLE_RATE, probe_seconds=PROBE_SECONDS, count=PROBES_PER_WINDOW):
    """Up to `count` probe clips of probe_seconds spread evenly over a window of `length` samples."""
    probe = int(probe_seconds * sr)
    if length <= probe * 3 // 2:
        return [(0, length)]
    count = max(1, min(count, length // probe))
    ranges = []
    for i in range(count):
        center = int((i + 0.5) * length / count)
        a = min(max(0, center - probe // 2), length - probe)
        ranges.append((a, a + probe))
    return ranges


def _normalized(text):
    return "".join(ch for ch in (text or "").lower() if ch.isalnum())


def is_repetitive(text):
    """A unit of 1-40 letters/digits repeated 4+ times in a row covers half the transcript."""
    norm = _normalized(text)
    if len(norm) < REPEAT_MIN_CHARS:
        return False
    longest = max((m.end() - m.start() for m in _REPEATED_UNIT.finditer(norm)), default=0)
    return longest >= REPEAT_COVERAGE * len(norm)


def degeneration(text, heard=()):
    """Why a window transcript looks degenerate, or None.

    `heard` are probe transcripts of clips inside the window in the same language; the full
    window must contain at least that speech. Silence or music-only probes hear nothing, so
    windows like that are never flagged for being short.
    """
    if is_repetitive(text):
        return "the same phrase repeats over most of the transcript"
    reference = sum(len(_normalized(t)) for t in heard)
    length = len(_normalized(text))
    if reference >= PROBE_MIN_CHARS and length < PROBE_COVERAGE * reference:
        return f"only {length} letters/digits, while shorter probe clips of it had {reference}"
    return None


def _vote(probes):
    """Most frequent probe language; ties go to the language with more recognized text."""
    if not probes:
        return None
    counts, amount = Counter(), Counter()
    for name, text in probes:
        counts[name] += 1
        amount[name] += len(_normalized(text))
    return max(counts, key=lambda name: (counts[name], amount[name]))


def token_budget(seconds):
    return min(MAX_NEW_TOKENS, TOKEN_MARGIN + math.ceil(seconds * TOKENS_PER_SECOND))


def probe_token_budget(seconds):
    return min(token_budget(seconds), PROBE_TOKEN_MARGIN + math.ceil(seconds * PROBE_TOKENS_PER_SECOND))


def probe_window(run, raw, a, b, seconds=PROBE_SECONDS, count=PROBES_PER_WINDOW):
    """Auto-language probe clips of raw[a:b] -> ([(language, text)] usable for voting, rejected count)."""
    probes, rejected = [], 0
    for pa, pb in probe_ranges(b - a, probe_seconds=seconds, count=count):
        lang, text = run(raw[a + pa:a + pb], None, probe_token_budget((pb - pa) / SAMPLE_RATE))
        name = primary_language(lang)
        if not text:
            continue
        # A looping probe says nothing reliable about the language.
        if name and not is_repetitive(text):
            probes.append((name, text))
        else:
            rejected += 1
    return probes, rejected


def plan_languages(run, raw, windows):
    """auto: [(language or None, [(language, probe text)])] per window from probe votes."""
    per_window, rejected = [], 0
    for a, b in windows:
        probes, bad = probe_window(run, raw, a, b)
        per_window.append(probes)
        rejected += bad
    overall = _vote([probe for probes in per_window for probe in probes])
    if overall is None and rejected:
        # Speech was heard but every probe looped or had no supported language: listening
        # without a language would repeat the failure, so try more, shorter clips first.
        rprint(f"[yellow]⚠️ All {rejected} language probe(s) were unusable; probing again with "
               f"{REPROBE_SECONDS} s clips...[/yellow]")
        per_window = [probe_window(run, raw, a, b, REPROBE_SECONDS, REPROBES_PER_WINDOW)[0] for a, b in windows]
        overall = _vote([probe for probes in per_window for probe in probes])
        if overall is None:
            raise ValueError("Qwen3-ASR could not determine the language: every probe clip looped or "
                             "returned an unsupported language. Set the recognition language explicitly.")
    plan = []
    for (a, b), probes in zip(windows, per_window):
        # A window whose probes heard nothing (e.g. music) follows the rest of the segment.
        language = _vote(probes) or overall
        votes = ", ".join(f"{name}×{n}" for name, n in Counter(name for name, _ in probes).items()) or "none"
        rprint(f"[cyan]🌐 {a / SAMPLE_RATE:.1f}-{b / SAMPLE_RATE:.1f}s language: {language or 'auto'} (probes: {votes})[/cyan]")
        plan.append((language, probes))
    return plan


def missed_speech(text, spoken):
    """Transcript far shorter than what auto-language probes heard (any language), or None."""
    reference = sum(len(_normalized(t)) for t in spoken)
    length = len(_normalized(text))
    if reference >= PROBE_MIN_CHARS and length < CROSS_LANGUAGE_COVERAGE * reference:
        return f"only {length} letters/digits, while auto-detected probe clips of it had {reference}"
    return None


# Scripts a transcript in each language is written in. Other languages Qwen3-ASR knows use Latin.
EXPECTED_SCRIPTS = {
    "zh": {"Han"}, "yue": {"Han"}, "ja": {"Han", "Kana"}, "ko": {"Hangul"},
    "ru": {"Cyrillic"}, "mk": {"Cyrillic"}, "el": {"Greek"}, "ar": {"Arabic"}, "fa": {"Arabic"},
    "hi": {"Devanagari"}, "th": {"Thai"},
}
_SCRIPT_PREFIXES = (("CJK", "Han"), ("IDEOGRAPHIC", "Han"), ("HIRAGANA", "Kana"), ("KATAKANA", "Kana"),
                    ("HALFWIDTH KATAKANA", "Kana"), ("HANGUL", "Hangul"), ("HALFWIDTH HANGUL", "Hangul"),
                    ("LATIN", "Latin"), ("FULLWIDTH LATIN", "Latin"), ("CYRILLIC", "Cyrillic"), ("GREEK", "Greek"),
                    ("ARABIC", "Arabic"), ("DEVANAGARI", "Devanagari"), ("THAI", "Thai"))
# One CJK character is about a syllable, roughly three Latin letters.
_SCRIPT_WEIGHT = {"Han": 3, "Kana": 3, "Hangul": 3}
# Conservative: only near-total mismatches, on enough text. zh with plenty of English words,
# en with a few CJK names, or ja written with many kanji stay well inside these limits.
SCRIPT_MIN_WEIGHT = 100
SCRIPT_MIN_SHARE = 0.2      # expected scripts must be at least 20% of the weighted letters
JA_MIN_KANA_SHARE = 0.05    # Japanese without kana (<5% of CJK letters) is Chinese
ZH_MAX_KANA_SHARE = 0.2     # "Chinese" with over 20% kana is Japanese
# Per-window check right after each forced window (fail on the first window instead of after
# the whole segment). A single window can legitimately be mostly another script (an English
# clip inside a Chinese video), so it only fails on near-total mismatches with plenty of text.
WINDOW_SCRIPT_LIMITS = {"min_weight": 300, "min_share": 0.05, "ja_min_kana": 0.02, "zh_max_kana": 0.5}


def script_counts(text):
    counts = Counter()
    for char in text or "":
        if not char.isalpha():
            continue
        try:
            name = unicodedata.name(char)
        except ValueError:
            continue
        for prefix, script in _SCRIPT_PREFIXES:
            if name.startswith(prefix):
                counts[script] += 1
                break
        else:
            counts["Other"] += 1
    return counts


def script_mismatch(text, iso, min_weight=SCRIPT_MIN_WEIGHT, min_share=SCRIPT_MIN_SHARE,
                    ja_min_kana=JA_MIN_KANA_SHARE, zh_max_kana=ZH_MAX_KANA_SHARE):
    """Why a transcript's writing system does not fit the selected language, or None (text only)."""
    counts = script_counts(text)
    weighted = {script: n * _SCRIPT_WEIGHT.get(script, 1) for script, n in counts.items()}
    total = sum(weighted.values())
    if total < min_weight:
        return None
    expected = EXPECTED_SCRIPTS.get(iso, {"Latin"})
    share = sum(weighted.get(script, 0) for script in expected) / total
    dominant = max(weighted, key=weighted.get)
    if share < min_share:
        return f"{1 - share:.0%} of the letters are not in the expected script ({dominant} text)"
    cjk = counts["Han"] + counts["Kana"]
    if cjk * 3 >= min_weight:
        kana = counts["Kana"] / cjk
        if iso == "ja" and kana < ja_min_kana:
            return f"only {kana:.0%} kana among the CJK characters (Chinese text)"
        if iso in ("zh", "yue") and kana > zh_max_kana:
            return f"{kana:.0%} kana among the CJK characters (Japanese text)"
    return None


def probe_mismatch(probes, language):
    """The language auto-detected probes heard instead of the selected one, or None."""
    reference = sum(len(_normalized(text)) for _, text in probes)
    if reference < PROBE_MIN_CHARS or any(iso_language(name) == iso_language(language) for name, _ in probes):
        return None
    return _vote(probes)


def language_mismatch_error(span, language, reason):
    return ValueError(
        f"Qwen3-ASR output for {span}: the selected recognition language ({language}) may not match the audio "
        f"({reason}). Use auto, or switch the Qwen3-ASR model size.")


def transcribe_window(run, raw, a, b, language, probes=None, offset=0.0, forced=False):
    """[(start, end, language, text)] for one window; retries shorter windows if degenerate.

    probes: auto-mode probe results for this window, or None (forced language) to probe
    lazily, only if the transcript is suspiciously sparse.
    """
    heard = [text for name, text in probes or () if name == language]
    seconds = (b - a) / SAMPLE_RATE
    listened = probes  # auto: the window's probes; forced: run lazily, only for suspicious output

    def listen():
        nonlocal listened
        if listened is None:
            listened = probe_window(run, raw, a, b)[0]
        return listened

    def check(text):
        reason = degeneration(text, heard)
        if reason or len(_normalized(text)) >= SPARSE_CHARS_PER_SECOND * seconds:
            return reason
        return missed_speech(text, [t for _, t in listen()])

    lang, text = run(raw[a:b], language)
    reason = check(text)
    if not reason:
        return [(a, b, lang, text)]
    span = f"{offset + a / SAMPLE_RATE:.1f}-{offset + b / SAMPLE_RATE:.1f}s"
    if forced:
        # A shorter retry can "succeed" in another language (1.7B forced to English wrote correct
        # Chinese in 60 s windows), which would then be aligned and split as the wrong language.
        # The probes (already run for sparse output; run now for loops) say what the audio is.
        heard_instead = probe_mismatch(listen(), language)
        if heard_instead:
            raise language_mismatch_error(
                span, language, f"{reason}; the probe clips sound like {heard_instead}")
    rprint(f"[yellow]⚠️ Qwen3-ASR output for {span} looks degenerate ({reason}); "
           f"retrying in {RETRY_WINDOW_SECONDS} s windows...[/yellow]")
    pieces = []
    parts = split_windows(raw[a:b], window_seconds=RETRY_WINDOW_SECONDS, search_seconds=RETRY_SEARCH_SECONDS)
    for sa, sb in parts:
        if sb - sa >= int(MIN_WINDOW_SECONDS * SAMPLE_RATE):
            sub_lang, sub_text = run(raw[a + sa:a + sb], language)
            pieces.append((a + sa, a + sb, sub_lang, sub_text))
    reason = next((degeneration(t) for *_, t in pieces if degeneration(t)), None) \
        or check(" ".join(t for *_, t in pieces))
    if reason:
        if forced:
            advice = (f"The selected recognition language ({language}) may not match the audio: "
                      "try auto, or the other Qwen3-ASR model size.")
        else:
            advice = ("Set the recognition language explicitly instead of auto, try the other "
                      "Qwen3-ASR model size, or check the audio.")
        raise ValueError(f"Qwen3-ASR output for {span} is still degenerate after retrying ({reason}). {advice}")
    return pieces


# ------------------------------------------------------------------
# Words: restore punctuation that the aligner strips
# ------------------------------------------------------------------

def _is_token_char(ch):
    # Qwen3ForceAlignProcessor keeps letters, numbers and apostrophes only.
    return ch == "'" or unicodedata.category(ch)[0] in "LN"


def attach_words(text, items, offset=0.0, limit=None):
    """Map aligner tokens back onto the ASR text so words keep punctuation.

    Aligner tokens are ordered subsequences of the text with punctuation removed
    ("U.S.," -> "US"); each word takes its token's span plus adjacent punctuation,
    e.g. "Hello, world." -> ["Hello,", "world."], "你好，世界。" -> ["你", "好，", "世", "界。"].
    Times are clamped to [0, limit] (the clip length): text longer than the audio, e.g. a
    window the model translated, made the aligner return times past the end of the audio.
    """
    def clamp(value):
        value = max(0.0, float(value))
        return min(value, limit) if limit is not None else value

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
            start, end = clamp(start), clamp(end)
            words.append({"word": surface, "start": round(offset + start, 3),
                          "end": round(offset + max(start, end), 3)})
            continue
        # Token not found in order (should not happen); keep its bare text without consuming the transcript.
        start, end = clamp(start), clamp(end)
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
    try:
        if engine == "mlx":
            import mlx.core as mx
            mx.clear_cache()
        else:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    except ImportError:
        pass  # the engine never loaded; keep the original error visible


def _torch_device():
    import torch
    if torch.cuda.is_available():
        dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        return "cuda:0", dtype
    return "cpu", torch.float32


@contextmanager
def asr_session(engine, repo_id):
    """Load Qwen3-ASR once and yield run(clip, qwen_language or None, max_tokens=None) -> (language, text)."""
    source = _model_source(repo_id)
    model = None
    try:
        if engine == "mlx":
            from mlx_audio.stt.utils import load_model
            model = load_model(source)

            def run(clip, language, max_tokens=None):
                check_cancel()
                out = model.generate(clip, language=language,
                                     max_tokens=max_tokens or token_budget(len(clip) / SAMPLE_RATE),
                                     chunk_duration=WINDOW_SECONDS + 1, min_chunk_duration=MIN_WINDOW_SECONDS)
                detected = language or ",".join(dict.fromkeys(l for l in (out.language or []) if l))
                return detected, out.text.strip()
        else:
            from qwen_asr import Qwen3ASRModel
            device, dtype = _torch_device()
            rprint(f"[cyan]🎮 Qwen3-ASR device:[/cyan] {device}, [cyan]dtype:[/cyan] {dtype}")
            model = Qwen3ASRModel.from_pretrained(source, dtype=dtype, device_map=device,
                                                  max_inference_batch_size=1, max_new_tokens=MAX_NEW_TOKENS)

            def run(clip, language, max_tokens=None):
                check_cancel()
                # qwen-asr reads this attribute for every generate() call.
                model.max_new_tokens = max_tokens or token_budget(len(clip) / SAMPLE_RATE)
                out = model.transcribe(audio=(clip, SAMPLE_RATE), language=language)[0]
                return language or out.language, out.text.strip()
        yield run
    finally:
        # Release the model even when a window fails, so a retry does not start out of memory.
        del model
        _free(engine)


def _transcribe(engine, repo_id, clips, language):
    """Return [(qwen_language_name, text)] per clip."""
    with asr_session(engine, repo_id) as run:
        return [run(clip, language) for clip in clips]


def _align(engine, repo_id, jobs):
    """jobs: [(clip, text, qwen_language)] -> [[(token, start, end)]] relative to each clip."""
    source = _model_source(repo_id)
    aligner, results = None, []
    try:
        if engine == "mlx":
            from mlx_audio.stt.utils import load_model
            aligner = load_model(source)
            align = lambda clip, text, lang: aligner.generate(clip, text=text, language=lang)
        else:
            from qwen_asr import Qwen3ForcedAligner
            device, dtype = _torch_device()
            aligner = Qwen3ForcedAligner.from_pretrained(source, dtype=dtype, device_map=device)
            align = lambda clip, text, lang: aligner.align(audio=(clip, SAMPLE_RATE), text=text, language=lang)[0]
        for clip, text, lang in jobs:
            check_cancel()
            result = align(clip, text, lang)
            results.append([(item.text, item.start_time, item.end_time) for item in result])
    finally:
        align = None  # the lambda holds a reference to the aligner
        del aligner
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
    if vocal_audio_file == raw_audio_file:
        vocal = raw
    else:
        # Windows are cut on the raw track, so the vocal track must use the same sample indices.
        vocal = match_length(load_audio_segment(vocal_audio_file, start, end), len(raw))
    # Drop slivers (< 0.1 s) left by segment boundaries; they carry no speech.
    windows = [(a, b) for a, b in split_windows(raw) if b - a >= int(MIN_WINDOW_SECONDS * SAMPLE_RATE)]

    # 1. transcribe raw audio (auto: probe the language first, then force it per window)
    t0 = time.time()
    pieces = []
    with asr_session(engine, models[size]) as run:
        plan = [(forced, None)] * len(windows) if forced else plan_languages(run, raw, windows)
        for (a, b), (language, probes) in zip(windows, plan):
            window = transcribe_window(run, raw, a, b, language, probes, start, forced=bool(forced))
            if forced:
                # Text only, no inference: a clearly wrong language fails on its first window.
                mismatch = script_mismatch(" ".join(text for *_, text in window), configured, **WINDOW_SCRIPT_LIMITS)
                if mismatch:
                    raise language_mismatch_error(
                        f"{start + a / SAMPLE_RATE:.1f}-{start + b / SAMPLE_RATE:.1f}s", forced, mismatch)
            pieces.extend(window)
    rprint(f"[cyan]⏱️ time transcribe:[/cyan] {time.time() - t0:.2f}s")

    if forced:
        # A wrong forced language often transcribes fine in the audio's own language (Korean
        # forced to English stays Korean). Checked on the text only, no extra inference; the
        # whole segment is checked with the looser limits after the per-window checks above.
        mismatch = script_mismatch(" ".join(text for *_, text in pieces), configured)
        if mismatch:
            raise language_mismatch_error(f"{start:.1f}-{end:.1f}s", forced, mismatch)
        detected = configured
    else:
        # Segment language for downstream steps: the language covering the most audio.
        votes = Counter()
        for a, b, lang, text in pieces:
            if text and iso_language(lang):
                votes[iso_language(lang)] += b - a
        detected = max(votes, key=votes.get) if votes else None
        if not detected and any(text for *_, text in pieces):
            raise ValueError("Qwen3-ASR could not detect the language; set the recognition language and retry.")

    # 2. align by vocal audio
    t0 = time.time()
    todo = [(a, b, text, (primary_language(lang) or ISO_TO_QWEN[detected]))
            for a, b, lang, text in pieces if text]
    jobs = [(vocal[a:b], text, lang) for a, b, text, lang in todo]
    aligned = _align(engine, models["aligner"], jobs) if jobs else []
    rprint(f"[cyan]⏱️ time align:[/cyan] {time.time() - t0:.2f}s")

    segments = []
    for (a, b, text, _), items in zip(todo, aligned):
        # Windows lie inside the decoded segment, so start + b / SAMPLE_RATE never passes the audio end.
        words = attach_words(text, items, start + a / SAMPLE_RATE, limit=(b - a) / SAMPLE_RATE)
        if words:
            segments.append({"text": text, "start": words[0]["start"],
                             "end": words[-1]["end"], "words": words})
    return {"language": detected, "segments": segments}
