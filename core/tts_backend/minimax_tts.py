import io
import requests
from pathlib import Path
from pydub import AudioSegment
from core.utils import load_key, except_handler

BASE_URL = "https://api.minimax.io/v1/t2a_v2"
BASE_URL_CN = "https://api.minimaxi.com/v1/t2a_v2"

VOICE_LIST = [
    "English_Graceful_Lady",
    "English_Insightful_Speaker",
    "English_radiant_girl",
    "English_Persuasive_Man",
    "English_Lucky_Robot",
    "Wise_Woman",
    "Friendly_Person",
    "Inspirational_girl",
    "Deep_Voice_Man",
    "sweet_girl",
    "cute_boy",
    "lovely_girl",
]

MODEL_LIST = ["speech-2.8-hd", "speech-2.8-turbo"]

# refer to: https://platform.minimax.io/docs/api-reference/speech-t2a-http

@except_handler("Failed to generate audio using MiniMax TTS", retry=3, delay=1)
def minimax_tts(text, save_path):
    API_KEY = load_key("minimax_tts.api_key")
    voice = load_key("minimax_tts.voice")
    model = load_key("minimax_tts.model")

    if voice not in VOICE_LIST:
        raise ValueError(f"Invalid voice: {voice}. Please choose from {VOICE_LIST}")

    payload = {
        "model": model,
        "text": text,
        "stream": False,
        "voice_setting": {
            "voice_id": voice,
            "speed": 1.0,
            "vol": 1.0,
            "pitch": 0,
        },
        "audio_setting": {
            "format": "mp3",
            "sample_rate": 32000,
        },
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(BASE_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()

    result = response.json()
    if "data" not in result or "audio" not in result["data"]:
        raise ValueError(f"Unexpected API response: {result}")

    audio_hex = result["data"]["audio"]
    audio_bytes = bytes.fromhex(audio_hex)

    # Convert mp3 to wav using pydub
    speech_file_path = Path(save_path)
    speech_file_path.parent.mkdir(parents=True, exist_ok=True)

    audio = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
    audio.export(save_path, format="wav")
    print(f"Audio saved to {speech_file_path}")


if __name__ == "__main__":
    minimax_tts("Hi! Welcome to VideoLingo!", "test.wav")
