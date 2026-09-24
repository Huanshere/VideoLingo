import json
import time

import requests
from rich import print as rprint

from core.asr_backend.audio_preprocess import audio_slice_wav
from core.utils import load_key, load_key_or, update_key

API_VERSION = "2025-10-15"
MODEL = "MAI-Transcribe-2"
ATTEMPTS = 3
RETRY_STATUS = {408, 429, 500, 502, 503, 504}
# Regions listing MAI-Transcribe in the Azure Speech region table.
REGIONS = ["eastus", "westus", "westus2", "northeurope", "southeastasia", "centralindia"]


def detect_region(api_key, regions=REGIONS, timeout=10):
    """Return the MAI region that accepts this key, or None.

    Speech keys are regional: the free STS token endpoint answers 200 only in the
    resource's own region, so no audio is sent and nothing is billed.
    """
    from concurrent.futures import ThreadPoolExecutor

    def accepts(region):
        try:
            response = requests.post(
                f"https://{region}.api.cognitive.microsoft.com/sts/v1.0/issueToken",
                headers={"Ocp-Apim-Subscription-Key": api_key, "Content-Length": "0"},
                timeout=timeout,
            )
            return response.status_code == 200
        except requests.RequestException:
            return False

    if not (api_key or "").strip():
        return None
    with ThreadPoolExecutor(len(regions)) as pool:
        results = list(pool.map(accepts, regions))
    return next((region for region, ok in zip(regions, results) if ok), None)


def transcription_url(region):
    """Build the Fast Transcription URL from a region name or a full resource endpoint."""
    region = (region or "").strip().rstrip("/")
    if region.startswith("https://"):
        base = region
    elif region and region.isalnum():
        base = f"https://{region.lower()}.api.cognitive.microsoft.com"
    else:
        raise ValueError("Set whisper.mai_region to an Azure Speech region such as eastus")
    return f"{base}/speechtotext/transcriptions:transcribe?api-version={API_VERSION}"


def request_definition(language):
    definition = {
        "enhancedMode": {
            "enabled": True,
            "model": MODEL,
            "modelOptions": {"timestamps": "word", "transcribeStyle": "clean"},
        }
    }
    if language and language != "auto":
        definition["locales"] = [language]
    return definition


def mai2whisper(result, offset=0.0):
    """Convert a MAI response into VideoLingo's WhisperX-style segments."""
    segments, locales = [], {}
    for phrase in result.get("phrases") or []:
        words = [
            {
                "word": word["text"],
                "start": offset + word["offsetMilliseconds"] / 1000,
                "end": offset + (word["offsetMilliseconds"] + word["durationMilliseconds"]) / 1000,
            }
            for word in phrase.get("words") or []
            if str(word.get("text", "")).strip()
        ]
        if not words:
            continue
        locale = phrase.get("locale")
        if locale:
            locales[locale] = locales.get(locale, 0) + len(words)
        segments.append({
            "text": phrase.get("text", "").strip(),
            "start": words[0]["start"],
            "end": words[-1]["end"],
            "words": words,
        })
    language = max(locales, key=locales.get).split("-")[0] if locales else None
    return {"segments": segments, "language": language}


def transcribe_audio_mai(raw_audio_path, vocal_audio_path, start=None, end=None):
    rprint(f"[cyan]🎤 Transcribing with {MODEL}: {vocal_audio_path}[/cyan]")
    audio = audio_slice_wav(vocal_audio_path, start, end)
    language = load_key("whisper.language")
    started = time.time()
    api_key = load_key("whisper.mai_api_key")
    region = str(load_key_or("whisper.mai_region", "") or "").strip()
    if not region:
        region = detect_region(api_key)
        if not region:
            raise ValueError("The Azure Speech key was not accepted in any MAI-Transcribe region; check whisper.mai_api_key.")
        update_key("whisper.mai_region", region)
    url = transcription_url(region)
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    definition = json.dumps(request_definition(language))
    for attempt in range(1, ATTEMPTS + 1):
        try:
            response = requests.post(
                url,
                headers=headers,
                files={
                    "audio": ("audio.wav", audio, "audio/wav"),
                    "definition": (None, definition, "application/json"),
                },
                timeout=600,
            )
        except (requests.ConnectionError, requests.Timeout) as error:
            if attempt == ATTEMPTS:
                raise
            rprint(f"[yellow]MAI-Transcribe connection failed ({error}); retrying {attempt}/{ATTEMPTS - 1}[/yellow]")
        else:
            if response.ok or response.status_code not in RETRY_STATUS or attempt == ATTEMPTS:
                break
            rprint(f"[yellow]MAI-Transcribe HTTP {response.status_code}; retrying {attempt}/{ATTEMPTS - 1}[/yellow]")
        time.sleep(5 * attempt)
    if not response.ok:
        raise RuntimeError(f"MAI-Transcribe request failed: HTTP {response.status_code} {response.text[:500]}")

    parsed = mai2whisper(response.json(), start or 0.0)
    if parsed["language"]:
        update_key("whisper.detected_language", parsed["language"])
    rprint(f"[green]✓ Transcription completed in {time.time() - started:.2f} seconds[/green]")
    return parsed
