from pathlib import Path
import requests
import json
from core.utils import load_key, except_handler

CAMB_API_BASE = "https://client.camb.ai/apis"

def _api_key():
    return load_key("camb_tts.api_key")

def _headers(content_type="application/json"):
    h = {"x-api-key": _api_key()}
    if content_type:
        h["Content-Type"] = content_type
    return h

@except_handler("Failed to generate audio using CAMB AI TTS", retry=3, delay=1)
def camb_tts(text, save_path):
    voice_id = int(load_key("camb_tts.voice_id"))
    language = load_key("camb_tts.language")
    model = load_key("camb_tts.model")

    payload = json.dumps({
        "text": text,
        "voice_id": voice_id,
        "language": language,
        "speech_model": model,
        "output_configuration": {"format": "wav"},
    })

    speech_file_path = Path(save_path)
    speech_file_path.parent.mkdir(parents=True, exist_ok=True)

    response = requests.post(
        f"{CAMB_API_BASE}/tts-stream",
        headers=_headers(),
        data=payload,
    )

    if response.status_code == 200:
        with open(speech_file_path, "wb") as f:
            f.write(response.content)
        print(f"Audio saved to {speech_file_path}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        raise RuntimeError(f"CAMB AI TTS failed: {response.status_code}")


if __name__ == "__main__":
    camb_tts("Hi! Welcome to VideoLingo!", "test_camb.wav")
