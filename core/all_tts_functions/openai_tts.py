from pathlib import Path
from openai import OpenAI
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# voice options: alloy, echo, fable, onyx, nova, and shimmer
# refer to: https://platform.openai.com/docs/guides/text-to-speech/quickstart
def openai_tts(text, save_path):
    from config import OAI_TTS_API_KEY, OAI_TTS_API_BASE_URL, OAI_VOICE

    client = OpenAI(
        base_url=OAI_TTS_API_BASE_URL.strip('/') + '/v1',
        api_key=OAI_TTS_API_KEY
    )

    speech_file_path = Path(save_path)
    # make dir before save
    speech_file_path.parent.mkdir(parents=True, exist_ok=True)
    with client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice=OAI_VOICE,
        input=text,

        response_format="wav"
    ) as response:
        response.stream_to_file(speech_file_path)
    
    print(f"Audio saved to {speech_file_path}")

if __name__ == "__main__":
    openai_tts("今天是个好日子，适合做点人们喜欢的东西！", "output/audio/tmp/test.wav")