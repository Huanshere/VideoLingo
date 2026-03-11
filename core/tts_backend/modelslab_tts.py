import time
import requests
from pathlib import Path

from core.utils import load_key, except_handler

# ModelsLab TTS API endpoints
_API_URL = "https://modelslab.com/api/v6/voice/text_to_speech"
_FETCH_URL = "https://modelslab.com/api/v6/voice/fetch/{}"

# Voice name → voice_id mapping
# Full list: https://docs.modelslab.com/text-to-audio/realtime/tts
VOICE_OPTIONS = {
    "Bella":   1,
    "Antoni":  2,
    "Elli":    3,
    "Josh":    4,
    "Arnold":  5,
    "Adam":    6,
    "Sam":     7,
    "Rachel":  8,
    "Domi":    9,
    "Gigi":    10,
}


@except_handler("Failed to generate audio using ModelsLab TTS", retry=3, delay=2)
def modelslab_tts(text: str, save_path: str) -> None:
    """
    Generate speech using the ModelsLab TTS API and save it as a WAV file.

    Config keys (in config.yaml under ``modelslab_tts``):
        api_key  — ModelsLab API key (https://modelslab.com)
        voice    — Voice name, one of: Bella, Antoni, Elli, Josh, Arnold, Adam,
                   Sam, Rachel, Domi, Gigi  (default: Bella)

    ModelsLab TTS has a 2 500-character limit per request.
    Responses with ``status == "processing"`` are polled every 5 s for up to 5 min.
    """
    api_key = load_key("modelslab_tts.api_key")
    voice_name = load_key("modelslab_tts.voice") or "Bella"

    if voice_name not in VOICE_OPTIONS:
        raise ValueError(
            f"Invalid voice '{voice_name}'. Choose from: {', '.join(VOICE_OPTIONS)}"
        )
    voice_id = VOICE_OPTIONS[voice_name]

    # Enforce API character limit
    if len(text) > 2500:
        text = text[:2500]

    payload = {
        "key": api_key,
        "prompt": text,
        "language": "English",
        "voice_id": voice_id,
        "audio_format": "wav",
    }

    response = requests.post(_API_URL, json=payload, timeout=(15, 60))
    response.raise_for_status()
    data = response.json()

    audio_url: str | None = None

    if data.get("status") == "success":
        output = data.get("output") or data.get("output_url")
        audio_url = output[0] if isinstance(output, list) else output

    elif data.get("status") == "processing":
        request_id = data.get("id")
        if not request_id:
            raise RuntimeError("ModelsLab returned 'processing' but no request id")

        fetch_url = _FETCH_URL.format(request_id)
        fetch_payload = {"key": api_key}

        for _ in range(60):          # poll for up to 5 minutes
            time.sleep(5)
            fetch_resp = requests.post(fetch_url, json=fetch_payload, timeout=(10, 30))
            fetch_resp.raise_for_status()
            fetch_data = fetch_resp.json()

            if fetch_data.get("status") == "success":
                output = fetch_data.get("output") or fetch_data.get("output_url")
                audio_url = output[0] if isinstance(output, list) else output
                break
            elif fetch_data.get("status") == "processing":
                continue
            else:
                raise RuntimeError(f"ModelsLab fetch error: {fetch_data}")

        if not audio_url:
            raise TimeoutError("ModelsLab TTS timed out waiting for audio generation")

    else:
        raise RuntimeError(f"ModelsLab TTS API error: {data}")

    # Download and save the generated audio
    audio_resp = requests.get(audio_url, timeout=(10, 120))
    audio_resp.raise_for_status()

    save_file = Path(save_path)
    save_file.parent.mkdir(parents=True, exist_ok=True)
    save_file.write_bytes(audio_resp.content)

    print(f"ModelsLab TTS: audio saved to {save_file}")


if __name__ == "__main__":
    modelslab_tts("Hello! This is a test of ModelsLab text-to-speech.", "test_modelslab.wav")
