from pathlib import Path
from openai import OpenAI
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.config_utils import load_key

# voice options: alloy, echo, fable, onyx, nova, and shimmer
# refer to: https://platform.openai.com/docs/guides/text-to-speech/quickstart
def openai_tts(text, save_path):
    oai_set = load_key("openai_tts")

    client = OpenAI(
        base_url=oai_set["base_url"].strip('/') + '/v1',
        api_key=oai_set["api_key"]
    )

    speech_file_path = Path(save_path)
    # make dir before save
    speech_file_path.parent.mkdir(parents=True, exist_ok=True)
    with client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice=oai_set["voice"],
        input=text,

        response_format="wav"
    ) as response:
        response.stream_to_file(speech_file_path)
    
    print(f"Audio saved to {speech_file_path}")

if __name__ == "__main__":
    openai_tts("今天是个好日子！", "openai_tts.wav")