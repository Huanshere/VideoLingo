from pathlib import Path
import requests
from core.utils import load_key, load_key_or, except_handler

# Any service with the speech endpoint of OpenAI. The defaults are those of OpenLux.
BASE_URL = "https://api.openlux.ai/v1"
MODEL = "gpt-4o-mini-tts"

# voices: alloy, ash, coral, echo, fable, nova, onyx, sage, shimmer, ...
# refer to: https://platform.openai.com/docs/guides/text-to-speech
@except_handler("Failed to generate audio using OpenAI TTS", retry=3, delay=1)
def openai_tts(text, save_path):
    base_url = load_key_or("openai_tts.base_url", BASE_URL).rstrip("/")
    payload = {
        "model": load_key_or("openai_tts.model", MODEL),
        "input": text,
        "voice": load_key("openai_tts.voice"),
        "response_format": "wav"
    }
    headers = {'Authorization': f"Bearer {load_key('openai_tts.api_key')}"}

    speech_file_path = Path(save_path)
    speech_file_path.parent.mkdir(parents=True, exist_ok=True)

    response = requests.post(f"{base_url}/audio/speech", headers=headers, json=payload)

    if response.status_code != 200:
        raise ValueError(f"OpenAI TTS request failed: HTTP {response.status_code} {response.text[:200]}")
    with open(speech_file_path, 'wb') as f:
        f.write(response.content)
    print(f"Audio saved to {speech_file_path}")

if __name__ == "__main__":
    openai_tts("Hi! Welcome to VideoLingo!", "test.wav")
