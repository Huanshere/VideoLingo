# coding=utf-8
import os,sys
import dashscope
from dashscope.audio.tts import SpeechSynthesizer
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.config_utils import load_key

def sambert_cloud(text: str, save_path: str):
    dashscope.api_key = load_key("sambert.api_key")
    model = load_key("sambert.api_key")
    result = SpeechSynthesizer.call(model=model,
                                text=text,
                                sample_rate=48000)
    if result.get_audio_data() is not None:
        with open(save_path, 'wb') as f:
            f.write(result.get_audio_data())
        print('SUCCESS: get audio data: %dbytes in %s' % (sys.getsizeof(result.get_audio_data()), save_path))
    else:
        print('ERROR: response is %s' % (result.get_response()))

if __name__ == "__main__":
    text = "Striking drums and gongs was also prohibited. Playing the huqin was also forbidden. Even playing secretly at home was forbidden."
    sambert_cloud(text, "output/cosyvoice-cloud.wav")