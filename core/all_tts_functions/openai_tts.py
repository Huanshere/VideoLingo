from pathlib import Path
from openai import OpenAI
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# voice options: alloy, echo, fable, onyx, nova, and shimmer
# refer to: https://platform.openai.com/docs/guides/text-to-speech/quickstart
def openai_tts(text, save_path):
    from config import API_KEY, BASE_URL, OAI_VOICE

    client = OpenAI(
        base_url=BASE_URL.strip('/') + '/v1',
        api_key=API_KEY
    )

    speech_file_path = Path(save_path)
    with client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice=OAI_VOICE,
        input=text,

        response_format="wav"
    ) as response:
        response.stream_to_file(speech_file_path)
    
    print(f"Audio saved to {speech_file_path}")

def oai_tts_for_videolingo(text, save_as, number, task_df):
    openai_tts(text, save_as)

# Example usage
# openai_tts("今天是个好日子，适合做点人们喜欢的东西！", "output/audio/tmp/test.wav")