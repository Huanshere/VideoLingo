"""FonadaLabs Kapture V3 cloud ASR with utterance-level timing and speaker labels.

Kapture V3 returns text without word timestamps. To keep subtitle timing genuine,
the audio is cut at pauses into short speech utterances (Silero VAD, already used
by the local backend) and each utterance is transcribed by its own request. Every
word of an utterance carries that utterance's measured span; no word timing is
interpolated. Speakers are assigned with SpeechBrain ECAPA embeddings clustered
across the whole recording.
"""

import hashlib
import io
import json
import time
import wave
from pathlib import Path

import numpy as np
import requests
from rich import print as rprint

from core.utils import check_cancel, load_key, load_key_or

API_URL = "https://api.fonada.ai/v3/asr/transcribe"
MODEL = "kapture-v3"
CACHE_IDENTITY = f"{MODEL}:utterance:v1"
BATCH_IDENTITY = f"{MODEL}:slots24:v1"
# Kapture V3 languages when this integration was written; Fonada validates the code itself.
LANGUAGES = {
    "en": "English", "hi": "हिन्दी (Hindi / Hinglish)", "bn": "বাংলা (Bengali)",
    "gu": "ગુજરાતી (Gujarati)", "kn": "ಕನ್ನಡ (Kannada)", "ml": "മലയാളം (Malayalam)",
    "mr": "मराठी (Marathi)", "or": "ଓଡ଼ିଆ (Odia)", "pa": "ਪੰਜਾਬੀ (Punjabi)",
    "ta": "தமிழ் (Tamil)", "te": "తెలుగు (Telugu)",
}
MAX_REQUEST_BYTES = 25_000_000
SAMPLE_RATE = 16000

# Utterances: speech regions joined across short pauses, cut before they grow too long
# for one subtitle cue. Silero splits a region at its longest internal pause when it
# exceeds MAX_UTTERANCE_SECONDS; a region with no pause at all is cut hard there.
TARGET_UTTERANCE_SECONDS = 6.0
MAX_UTTERANCE_SECONDS = 10.0
JOIN_GAP_SECONDS = 0.5
EDGE_PADDING_SECONDS = 0.15
MIN_UTTERANCE_SECONDS = 0.25

# Batching. Fonada cuts every upload itself into 20-28 s chunks, searching 20-28 s after
# each chunk start for silence and cutting in its middle (common/audio_chunker.py,
# _mvad_chunk_boundaries). Each phrase is placed in its own 24 s slot - 4 s silence,
# the phrase (<= 16 s), silence - so the 8 s of silence between phrases is exactly the
# 20-28 s search window: every cut lands on a slot edge and every returned chunk is one
# phrase. Responses are checked against this layout and rejected if they differ.
SLOT_SECONDS = 24.0
SLOT_LEAD_SECONDS = 4.0
SLOT_MAX_PHRASE_SECONDS = 16.0
SLOT_TOLERANCE_SECONDS = 0.1
BATCH_SLOTS = 100
BATCH_TIMEOUT_SECONDS = 900

# Requests
TIMEOUT_SECONDS = 60
ATTEMPTS = 3
MAX_RETRY_AFTER_SECONDS = 120
# Fonada limits requests per key per minute (10 on the plan this was tested with);
# whisper.fonada_requests_per_minute overrides it for plans with a higher limit.
DEFAULT_REQUESTS_PER_MINUTE = 10
RATE_LIMIT_WAITS = 5

# Speakers: adjacent regions are joined only when they sound like the same speaker.
SAME_SPEAKER_SIMILARITY = 0.55
CHANGE_WINDOW_SECONDS = 1.5
# Window similarity below which the voice changed (lower = fewer false cuts in one voice).
CHANGE_SIMILARITY = 0.25
CHANGE_HOP_SECONDS = 0.5
CLUSTER_DISTANCE = 0.65
# Embeddings of shorter utterances are too noisy to found a speaker; they join the nearest one.
RELIABLE_SECONDS = 1.5
# A detected speaker needs this much speech, absolute and as a share of all speech.
MIN_SPEAKER_SECONDS = 8.0
MIN_SPEAKER_SHARE = 0.02
EMBEDDING_MODEL = "speechbrain/spkrec-ecapa-voxceleb"

CHECKPOINT_DIR = Path(".cache/asr/fonada")


class FonadaError(RuntimeError):
    pass


class RateLimiter:
    """At most `per_minute` request starts in any 60 s window, shared by all threads."""

    def __init__(self, per_minute, clock=time.monotonic, sleep=time.sleep):
        import threading
        self.per_minute, self.clock, self.sleep = max(1, int(per_minute)), clock, sleep
        self.starts, self.lock = [], threading.Lock()

    def wait(self):
        while True:
            with self.lock:
                now = self.clock()
                self.starts = [t for t in self.starts if now - t < 60]
                if len(self.starts) < self.per_minute:
                    self.starts.append(now)
                    return
                delay = 60 - (now - self.starts[0]) + 0.5
            check_cancel()
            self.sleep(min(delay, 5))

    def penalize(self):
        """Fonada said the window is full: treat it as full for the next minute."""
        with self.lock:
            now = self.clock()
            self.starts = [now] * self.per_minute


_limiter = None


def rate_limiter():
    global _limiter
    per_minute = int(load_key_or("whisper.fonada_requests_per_minute", DEFAULT_REQUESTS_PER_MINUTE)
                     or DEFAULT_REQUESTS_PER_MINUTE)
    if _limiter is None or _limiter.per_minute != per_minute:
        _limiter = RateLimiter(per_minute)
    return _limiter


# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

def configured_credentials():
    """Fail before preparing media when the key or language is unusable."""
    api_key = str(load_key_or("whisper.fonada_api_key", "") or "").strip()
    if not api_key or api_key.lower().startswith(("your_", "your ")):
        raise ValueError("Set whisper.fonada_api_key before using FonadaLabs ASR")
    language = str(load_key("whisper.language") or "").strip().lower()
    if not language or language == "auto":
        raise ValueError("FonadaLabs ASR needs an explicit recognition language "
                         f"(one of {', '.join(LANGUAGES)}); set whisper.language")
    return api_key, language


# ------------------------------------------------------------------
# Audio
# ------------------------------------------------------------------

def load_audio(path, start, end):
    from core.asr_backend.qwen_asr_local import load_audio_segment
    return load_audio_segment(path, start, end)


def wav_bytes(samples):
    pcm = (np.clip(samples, -1.0, 1.0) * 32767).astype("<i2").tobytes()
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(SAMPLE_RATE)
        out.writeframes(pcm)
    return buffer.getvalue()


def speech_regions(audio):
    """Silero speech regions [(start, end)] in samples."""
    import torch
    threads = torch.get_num_threads()
    try:
        torch.set_num_threads(1)
        from silero_vad import load_silero_vad, get_speech_timestamps
        regions = get_speech_timestamps(
            torch.from_numpy(audio), load_silero_vad(), sampling_rate=SAMPLE_RATE,
            threshold=0.4, min_speech_duration_ms=150, min_silence_duration_ms=150,
            max_speech_duration_s=MAX_UTTERANCE_SECONDS, speech_pad_ms=0,
            progress_tracking_callback=lambda _: check_cancel(),
        )
    finally:
        torch.set_num_threads(threads)
    return [(r["start"], r["end"]) for r in regions]


def plan_utterances(regions, total, same_speaker=None, sr=SAMPLE_RATE):
    """Join speech regions into utterances [(start, end)] in samples.

    Neighbouring regions are joined across pauses shorter than JOIN_GAP_SECONDS while
    the result stays within TARGET_UTTERANCE_SECONDS and, when `same_speaker(i)` is
    given, region i and i+1 sound like one speaker. Edges get a little padding that
    never crosses into a neighbour, so soft word onsets are kept.
    """
    groups = []
    for i, (a, b) in enumerate(regions):
        if groups:
            ga, gb = groups[-1]
            joinable = ((a - gb) < JOIN_GAP_SECONDS * sr and (b - ga) <= TARGET_UTTERANCE_SECONDS * sr
                        and (same_speaker is None or same_speaker(i - 1)))
            if joinable:
                groups[-1] = (ga, b)
                continue
        groups.append((a, b))
    groups = [(a, b) for a, b in groups if b - a >= MIN_UTTERANCE_SECONDS * sr]
    pad = int(EDGE_PADDING_SECONDS * sr)
    planned = []
    for i, (a, b) in enumerate(groups):
        # Each side of a gap pads at most half of it, so requests never share audio.
        lo = max(0, a - pad, (groups[i - 1][1] + a) // 2 if i else 0)
        hi = min(total, b + pad, (b + groups[i + 1][0]) // 2 if i + 1 < len(groups) else total)
        planned.append((lo, hi))
    return planned


# ------------------------------------------------------------------
# Speakers
# ------------------------------------------------------------------

_encoder = None


def speaker_encoder():
    global _encoder
    if _encoder is None:
        import torch
        from speechbrain.inference.speaker import EncoderClassifier
        device = "cuda" if torch.cuda.is_available() else "cpu"
        savedir = Path(load_key_or("model_dir", "_model_cache")) / "spkrec-ecapa-voxceleb"
        _encoder = EncoderClassifier.from_hparams(
            source=EMBEDDING_MODEL, savedir=str(savedir), run_opts={"device": device})
    return _encoder


def embed(audio, spans):
    """Unit-length ECAPA embedding per span."""
    import torch
    encoder = speaker_encoder()
    out = []
    with torch.no_grad():
        for a, b in spans:
            check_cancel()
            clip = torch.from_numpy(audio[a:b]).unsqueeze(0)
            vector = encoder.encode_batch(clip).squeeze().cpu().numpy().astype(np.float64)
            out.append(vector / (np.linalg.norm(vector) or 1.0))
    return out


def window_embeddings(audio, starts, length):
    """Unit embeddings of equal-length windows, batched."""
    import torch
    encoder = speaker_encoder()
    out = []
    with torch.no_grad():
        for i in range(0, len(starts), 64):
            check_cancel()
            batch = torch.from_numpy(np.stack([audio[s:s + length] for s in starts[i:i + 64]]))
            vectors = encoder.encode_batch(batch).squeeze(1).cpu().numpy().astype(np.float64)
            out.extend(vectors / np.maximum(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-9))
    return out


def split_speaker_changes(audio, regions, sr=SAMPLE_RATE):
    """Cut speech regions where the voice changes without a pause.

    Windows of CHANGE_WINDOW_SECONDS slide through each long region; where neighbouring
    windows sound like different speakers, the region is cut at the quietest 20 ms
    near the change so that no request mixes two speakers.
    """
    window, hop = int(CHANGE_WINDOW_SECONDS * sr), int(CHANGE_HOP_SECONDS * sr)
    jobs = [(r, list(range(r[0], r[1] - window + 1, hop))) for r in regions if r[1] - r[0] >= 2 * window]
    starts = [s for _, ss in jobs for s in ss]
    vectors = iter(window_embeddings(audio, starts, window) if starts else [])
    cuts = {}
    for region, ss in jobs:
        vs = [next(vectors) for _ in ss]
        points = []
        for k in range(1, len(vs)):
            # Compare windows that do not overlap, so a change shows as a dip.
            j = k + int(np.ceil(window / hop)) - 1
            if j < len(vs) and float(vs[k - 1] @ vs[j]) < CHANGE_SIMILARITY:
                centre = (ss[k - 1] + window + ss[j]) // 2
                if not points or centre - points[-1] >= window:
                    points.append(centre)
        cuts[region] = [quietest(audio, p, int(0.5 * sr), sr) for p in points]
    out = []
    for a, b in regions:
        edges = [a, *[c for c in cuts.get((a, b), []) if a + sr // 2 < c < b - sr // 2], b]
        out.extend(zip(edges, edges[1:]))
    return out


def quietest(audio, centre, reach, sr=SAMPLE_RATE):
    frame = sr // 50
    lo, hi = max(0, centre - reach), min(len(audio), centre + reach)
    if hi - lo < frame:
        return centre
    energy = [float(np.mean(audio[s:s + frame] ** 2)) for s in range(lo, hi - frame + 1, frame)]
    return lo + int(np.argmin(energy)) * frame + frame // 2


def cluster_speakers(embeddings, durations=None, num_speakers=None):
    """Global speaker labels for unit embeddings.

    Only utterances long enough for a reliable embedding form clusters (agglomerative,
    cosine, average linkage). Clusters holding too little speech to be a real speaker
    are absorbed, then every utterance takes the nearest remaining speaker centroid.
    """
    if not embeddings:
        return []
    X = np.vstack(embeddings)
    durations = np.ones(len(X)) * RELIABLE_SECONDS if durations is None else np.asarray(durations, float)
    reliable = np.flatnonzero(durations >= RELIABLE_SECONDS)
    if len(reliable) < 2:
        reliable = np.argsort(-durations)[:max(1, min(len(X), 2))]
    if len(reliable) == 1:
        return [0] * len(X)
    from sklearn.cluster import AgglomerativeClustering
    if num_speakers:
        model = AgglomerativeClustering(n_clusters=min(int(num_speakers), len(reliable)),
                                        metric="cosine", linkage="average")
    else:
        model = AgglomerativeClustering(n_clusters=None, distance_threshold=CLUSTER_DISTANCE,
                                        metric="cosine", linkage="average")
    seed = model.fit_predict(X[reliable])
    speech = {c: durations[reliable][seed == c].sum() for c in set(seed)}
    keep = [c for c in speech if num_speakers or speech[c] >= max(MIN_SPEAKER_SECONDS,
                                                                    MIN_SPEAKER_SHARE * sum(speech.values()))]
    keep = keep or [max(speech, key=speech.get)]
    centroids = np.vstack([X[reliable][seed == c].mean(axis=0) for c in keep])
    centroids /= np.linalg.norm(centroids, axis=1, keepdims=True)
    labels = (X @ centroids.T).argmax(axis=1)
    # Number speakers in order of first appearance.
    order = {}
    return [order.setdefault(label, len(order)) for label in labels]


def assign_speakers(segments, num_speakers=None):
    """Label segments carrying `speaker_embedding` with SPEAKER_nn; drops the embeddings."""
    indexed = [(i, s.pop("speaker_embedding")) for i, s in enumerate(segments) if s.get("speaker_embedding")]
    durations = [segments[i]["end"] - segments[i]["start"] for i, _ in indexed]
    labels = cluster_speakers([np.asarray(e) for _, e in indexed], durations, num_speakers)
    for (i, _), label in zip(indexed, labels):
        segments[i]["speaker_id"] = f"SPEAKER_{label:02d}"
    for segment in segments:
        segment.pop("speaker_embedding", None)
    return segments


# ------------------------------------------------------------------
# Requests
# ------------------------------------------------------------------

def _error_code(response):
    try:
        body = response.json()
    except ValueError:
        return "", ""
    detail = body.get("detail", body) if isinstance(body, dict) else {}
    if isinstance(detail, dict):
        return str(detail.get("error") or ""), str(detail.get("message") or "")
    return "", str(detail)


def response_text(body):
    """Transcript text from Fonada's JSON (top level or nested `result`)."""
    if not isinstance(body, dict):
        return ""
    for key in ("text", "transcript", "transcription", "result"):
        value = body.get(key)
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, dict):
            nested = response_text(value)
            if nested:
                return nested
    return ""


MESSAGES = {
    401: "FonadaLabs rejected the API key",
    403: "FonadaLabs denied access for this key",
    413: "The audio is larger than FonadaLabs accepts",
}


def transcribe_clip(api_key, language, audio_wav, label="", session=requests, limiter=None):
    """One Fonada request -> transcript text ('' when Fonada heard no speech)."""
    body = post_audio(api_key, language, ("utterance.wav", audio_wav, "audio/wav"), label, session, limiter)
    return response_text(body) if body is not None else ""


def post_audio(api_key, language, file, label="", session=requests, limiter=None, timeout=TIMEOUT_SECONDS):
    """POST one upload; the JSON body, or None when Fonada heard no speech at all."""
    audio = file[1]
    if not audio or len(audio) > MAX_REQUEST_BYTES:
        raise FonadaError(f"{label}: request of {len(audio)} bytes is outside FonadaLabs' 1..{MAX_REQUEST_BYTES} byte limit")
    limiter = limiter or rate_limiter()
    attempt, waits = 1, 0
    while True:
        check_cancel()
        limiter.wait()
        try:
            response = session.post(
                API_URL, headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
                files={"file": file}, data={"language_id": language}, timeout=timeout,
            )
        except (requests.ConnectionError, requests.Timeout) as error:
            if attempt == ATTEMPTS:
                raise FonadaError(f"{label}: FonadaLabs request failed after {ATTEMPTS} attempts ({type(error).__name__})") from None
            rprint(f"[yellow]FonadaLabs {label}: {type(error).__name__}; retry {attempt}/{ATTEMPTS - 1}[/yellow]")
            time.sleep(2 * attempt)
            attempt += 1
            continue
        if response.ok:
            return response.json()
        code, message = _error_code(response)
        status = response.status_code
        if code == "empty_transcript":
            return None
        if code == "credits_exhausted":
            raise FonadaError("FonadaLabs credits are exhausted; top up and run again (finished utterances are kept)")
        if code == "unsupported_language" or (status == 400 and "language" in code):
            raise FonadaError(f"FonadaLabs does not support language_id '{language}'. Supported: {', '.join(LANGUAGES)}")
        if status == 429 and code in ("rate_limit_exceeded", "concurrent_limit_exceeded", ""):
            # Not an error of this request: wait for the window to clear, without using attempts.
            waits += 1
            if waits > RATE_LIMIT_WAITS:
                raise FonadaError(f"{label}: FonadaLabs kept rate-limiting this key; lower "
                                  "whisper.fonada_requests_per_minute and run again (finished phrases are kept)")
            try:
                wait = min(MAX_RETRY_AFTER_SECONDS, max(60.0, float(response.headers.get("Retry-After", 60))))
            except ValueError:
                wait = 60.0
            limiter.penalize()
            rprint(f"[yellow]FonadaLabs {label}: rate limited ({message or code}); waiting {wait:.0f}s[/yellow]")
            time.sleep(wait)
            continue
        if status < 500 or attempt == ATTEMPTS:
            reason = MESSAGES.get(status) or f"FonadaLabs HTTP {status} {code}".strip()
            detail = (message or "")[:200].replace(api_key, "[REDACTED]")
            raise FonadaError(f"{label}: {reason}{': ' + detail if detail else ''}")
        rprint(f"[yellow]FonadaLabs {label}: HTTP {status} {code}; retry {attempt}/{ATTEMPTS - 1}[/yellow]")
        time.sleep(2 * attempt)
        attempt += 1


def slot_layout(clips, sr=SAMPLE_RATE):
    """Pack phrase clips into one 24 s slot each; returns float32 audio."""
    slot, lead = int(SLOT_SECONDS * sr), int(SLOT_LEAD_SECONDS * sr)
    out = np.zeros(slot * len(clips), dtype=np.float32)
    for k, clip in enumerate(clips):
        if len(clip) > SLOT_MAX_PHRASE_SECONDS * sr:
            raise ValueError(f"phrase of {len(clip) / sr:.1f}s does not fit a {SLOT_SECONDS:.0f}s slot")
        out[k * slot + lead:k * slot + lead + len(clip)] = clip
    return out


def flac_bytes(samples, sr=SAMPLE_RATE):
    import soundfile as sf
    buffer = io.BytesIO()
    sf.write(buffer, samples, sr, format="FLAC", subtype="PCM_16")
    return buffer.getvalue()


def slot_texts(body, count):
    """Per-slot texts from Fonada's transcript_chunks, or FonadaError if the layout differs."""
    if body is None:
        return [""] * count
    if count == 1:
        return [response_text(body)]
    chunks = body.get("transcript_chunks") if isinstance(body, dict) else None
    if not isinstance(chunks, list) or len(chunks) != count:
        raise FonadaError(f"FonadaLabs split a batch of {count} phrases into "
                          f"{len(chunks) if isinstance(chunks, list) else 'no'} chunks; "
                          "its server-side chunking changed, so phrase texts cannot be assigned safely")
    texts = []
    for k, chunk in enumerate(sorted(chunks, key=lambda c: float(c.get("start_s", 0)))):
        start = float(chunk.get("start_s", -1))
        if abs(start - k * SLOT_SECONDS) > SLOT_TOLERANCE_SECONDS:
            raise FonadaError(f"FonadaLabs chunk {k} starts at {start:.2f}s instead of "
                              f"{k * SLOT_SECONDS:.2f}s; phrase texts cannot be assigned safely")
        texts.append(str(chunk.get("text") or "").strip())
    return texts


def transcribe_batch(api_key, language, clips, label="", session=requests, limiter=None):
    """Texts for several phrase clips from one Fonada request."""
    audio = slot_layout(clips)
    data = flac_bytes(audio)
    if len(data) > MAX_REQUEST_BYTES and len(clips) > 1:
        half = len(clips) // 2
        return (transcribe_batch(api_key, language, clips[:half], label, session, limiter)
                + transcribe_batch(api_key, language, clips[half:], label, session, limiter))
    body = post_audio(api_key, language, ("phrases.flac", data, "audio/flac"), label, session, limiter,
                      timeout=BATCH_TIMEOUT_SECONDS)
    return slot_texts(body, len(clips))


def _checkpoint_path(audio_wav, language):
    digest = hashlib.sha256(audio_wav + f"\0{language}\0{CACHE_IDENTITY}".encode()).hexdigest()
    return CHECKPOINT_DIR / f"{digest}.json"


def transcribe_cached(api_key, language, audio_wav, label, use_cache=True):
    """Utterance requests are content-addressed, so a failed long run resumes unbilled."""
    path = _checkpoint_path(audio_wav, language)
    if use_cache and path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))["text"]
    text = transcribe_clip(api_key, language, audio_wav, label)
    if use_cache:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"text": text}, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)
    return text


# ------------------------------------------------------------------
# VideoLingo entry point
# ------------------------------------------------------------------

def utterance_segment(text, start, end):
    """A segment whose every word carries the utterance's measured span."""
    words = [{"word": w, "start": start, "end": end} for w in text.split()]
    return {"text": text, "start": start, "end": end, "words": words}


def transcribe_audio_fonada(raw_audio_path, vocal_audio_path, start=None, end=None):
    api_key, language = configured_credentials()
    start = float(start or 0.0)
    if end is None:
        from core.asr_backend.audio_preprocess import get_audio_duration
        end = get_audio_duration(vocal_audio_path)
    started = time.time()
    audio = load_audio(vocal_audio_path, start, end)
    check_cancel()

    regions = split_speaker_changes(audio, speech_regions(audio))
    region_embeddings = embed(audio, regions) if len(regions) > 1 else []
    same = (lambda i: float(region_embeddings[i] @ region_embeddings[i + 1]) >= SAME_SPEAKER_SIMILARITY) \
        if region_embeddings else None
    utterances = plan_utterances(regions, len(audio), same)
    rprint(f"[cyan]FonadaLabs: {len(regions)} speech regions -> {len(utterances)} utterance requests "
           f"for {start:.1f}-{end:.1f}s[/cyan]")

    use_cache = bool(load_key_or("whisper.cache", True))
    texts = [None] * len(utterances)
    todo = []
    for i, (a, b) in enumerate(utterances):
        path = _checkpoint_path(wav_bytes(audio[a:b]), language)
        if use_cache and path.is_file():
            texts[i] = json.loads(path.read_text(encoding="utf-8"))["text"]
        else:
            todo.append(i)
    batches = [todo[k:k + BATCH_SLOTS] for k in range(0, len(todo), BATCH_SLOTS)]
    rprint(f"[cyan]FonadaLabs: {len(utterances) - len(todo)} phrases cached, {len(todo)} to send in "
           f"{len(batches)} request(s); billed audio ~{len(todo) * SLOT_SECONDS / 60:.1f} min "
           f"(each phrase is padded to a {SLOT_SECONDS:.0f}s slot)[/cyan]")
    for n, batch in enumerate(batches, 1):
        check_cancel()
        first, last = utterances[batch[0]], utterances[batch[-1]]
        label = (f"batch {n}/{len(batches)} ({start + first[0] / SAMPLE_RATE:.1f}-"
                 f"{start + last[1] / SAMPLE_RATE:.1f}s, {len(batch)} phrases)")
        t0 = time.time()
        results = transcribe_batch(api_key, language, [audio[utterances[i][0]:utterances[i][1]] for i in batch], label)
        rprint(f"[cyan]FonadaLabs {label}: done in {time.time() - t0:.1f}s[/cyan]")
        for i, text in zip(batch, results):
            texts[i] = text
            if use_cache:
                a, b = utterances[i]
                path = _checkpoint_path(wav_bytes(audio[a:b]), language)
                path.parent.mkdir(parents=True, exist_ok=True)
                tmp = path.with_suffix(".tmp")
                tmp.write_text(json.dumps({"text": text}, ensure_ascii=False), encoding="utf-8")
                tmp.replace(path)

    kept = [(span, text) for span, text in zip(utterances, texts) if text]
    vectors = embed(audio, [span for span, _ in kept])
    segments = []
    for ((a, b), text), vector in zip(kept, vectors):
        segment = utterance_segment(text, round(start + a / SAMPLE_RATE, 3), round(start + b / SAMPLE_RATE, 3))
        segment["speaker_embedding"] = [round(float(v), 6) for v in vector]
        segments.append(segment)
    rprint(f"[green]✓ FonadaLabs transcribed {len(kept)}/{len(utterances)} utterances "
           f"in {time.time() - started:.1f}s[/green]")
    return {"segments": segments, "language": language}
