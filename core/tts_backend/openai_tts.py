from pathlib import Path
import requests
import json
from core.utils import load_key, except_handler

BASE_URL = "https://api.openai.com/v1/audio/speech"
VOICE_LIST = ["alloy", "ash", "ballad", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer", "verse"]
# voice options: alloy, ash, ballad, coral, echo, fable, onyx, nova, sage, shimmer, and verse
# refer to: https://platform.openai.com/docs/guides/text-to-speech/quickstart
@except_handler("Failed to generate audio using OpenAI TTS", retry=3, delay=1)
def openai_tts(text, save_path):
    API_KEY = load_key("openai_tts.api_key")
    voice = load_key("openai_tts.voice")
    payload = json.dumps({
        "model": "gpt-4o-mini-tts",
        "input": text,
        "voice": voice,
        "instructions": "Speak in a cheerful and positive tone.",
        "response_format": "wav"
    })
    
    if voice not in VOICE_LIST:
        raise ValueError(f"Invalid voice: {voice}. Please choose from {VOICE_LIST}")
    headers = {'Authorization': f"Bearer {API_KEY}", 'Content-Type': 'application/json'}
    
    speech_file_path = Path(save_path)
    speech_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    response = requests.post(BASE_URL, headers=headers, data=payload)
    
    if response.status_code == 200:
        with open(speech_file_path, 'wb') as f:
            f.write(response.content)
        print(f"Audio saved to {speech_file_path}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    openai_tts("Hi! Welcome to VideoLingo!", "test.wav")