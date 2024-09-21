import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import azure.cognitiveservices.speech as speechsdk

def azure_tts(text, savepath):
    from config import AZURE_KEY, AZURE_REGION, AZURE_VOICE
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_KEY, region=AZURE_REGION)
    audio_config = speechsdk.audio.AudioOutputConfig(filename=savepath)

    # The neural multilingual voice can speak different languages based on the input text.
    speech_config.speech_synthesis_voice_name=AZURE_VOICE

    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()

    if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print(f"Audio saved successfully to {savepath}")
    elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        print(f"Speech synthesis canceled: {speech_synthesis_result.cancellation_details.reason}")
        if speech_synthesis_result.cancellation_details.error_details:
            print(f"Error: {speech_synthesis_result.cancellation_details.error_details}")
        return False

def azure_tts_for_videolingo(text, save_as, number, task_df):
    azure_tts(text, save_as)

azure_tts("你好，世界！", "output/audio/azure_tts.wav")