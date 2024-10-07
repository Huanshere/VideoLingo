import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
import azure.cognitiveservices.speech as speechsdk
from core.config_utils import load_key

def azure_tts(text, savepath):
    azure_set = load_key("azure_tts")
    speech_config = speechsdk.SpeechConfig(subscription=azure_set["key"], region=azure_set["region"])
    audio_config = speechsdk.audio.AudioOutputConfig(filename=savepath)

    # The neural multilingual voice can speak different languages based on the input text.
    speech_config.speech_synthesis_voice_name=azure_set["voice"]

    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()

    if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print(f"Audio saved successfully to {savepath}")
    elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        print(f"Speech synthesis canceled: {speech_synthesis_result.cancellation_details.reason}")
        if speech_synthesis_result.cancellation_details.error_details:
            print(f"Error: {speech_synthesis_result.cancellation_details.error_details}")
        return False

if __name__ == "__main__":
    azure_tts("你好，世界！", "azure_tts.wav")