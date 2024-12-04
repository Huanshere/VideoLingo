# coding=utf-8
import os, sys
import dashscope
from dashscope.audio.tts_v2 import *
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.config_utils import load_key

def cosyvoice_cloud(text: str, save_path: str):
    dashscope.api_key = load_key("cosyvoice_cloud.api_key")
    model = "cosyvoice-v1"
    voice = load_key("cosyvoice_cloud.speaker")
    speech_rate = float(load_key("cosyvoice_cloud.speed"))
    synthesizer = SpeechSynthesizer(model=model, voice=voice, speech_rate=speech_rate, format=AudioFormat.WAV_22050HZ_MONO_16BIT)
    audio = synthesizer.call(text)
    print('requestId: ', synthesizer.get_last_request_id())
    with open(save_path, 'wb') as f:
        f.write(audio)

if __name__ == "__main__":
    text = """操作柔软物体非常难"""
    cosyvoice_cloud(text, "output/cosyvoice-cloud.wav")