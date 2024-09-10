import os
import sys
import replicate
import pandas as pd
import json
from typing import Dict
import subprocess
import base64
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def convert_video_to_audio(input_file: str) -> str:
    os.makedirs('output/audio', exist_ok=True)
    audio_file = 'output/audio/raw_full_audio.wav'
    
    if not os.path.exists(audio_file):
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', input_file,
            '-vn',
            '-acodec', 'libmp3lame',
            '-ar', '16000',
            '-b:a', '64k',
            audio_file
        ]
        print(f"🎬➡️🎵 Converting to audio......")
        subprocess.run(ffmpeg_cmd, check=True, stderr=subprocess.PIPE)
        print(f"🎬➡️🎵 Converted <{input_file}> to <{audio_file}>\n")
    
    return audio_file

def encode_file_to_base64(file_path: str) -> str:
    print("🔄 Encoding audio file to base64...")
    with open(file_path, 'rb') as file:
        encoded = base64.b64encode(file.read()).decode('utf-8')
        print("✅ File successfully encoded to base64")
        return encoded

def transcribe_audio(audio_base64: str) -> Dict:
    from config import WHISPER_LANGUAGE
    from config import REPLICATE_API_TOKEN
    # Set API token
    os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN
    print(f"🚀 Starting WhisperX API... Sometimes it takes time for the official server to start, please wait patiently... Actual processing speed is 10s for 2min audio, costing about ¥0.1 per run")
    try:
        input_params = {
            "debug": False,
            "vad_onset": 0.5,
            "audio_file": f"data:audio/wav;base64,{audio_base64}",
            "batch_size": 64,
            "vad_offset": 0.363,
            "diarization": False,
            "temperature": 0,
            "align_output": True,
            "language_detection_min_prob": 0,
            "language_detection_max_tries": 5
        }
        
        if WHISPER_LANGUAGE != 'auto':
            input_params["language"] = WHISPER_LANGUAGE
        
        output = replicate.run(
            "victor-upmeet/whisperx:84d2ad2d6194fe98a17d2b60bef1c7f910c46b2f6fd38996ca457afd9c8abfcb",
            input=input_params
        )
        return output
    except Exception as e:
        raise Exception(f"Error accessing whisperX API: {e} \n Cuda errors are caused by issues with the official API's server instance. Please wait for five minutes to allow the official server to switch, then try again.")

def process_transcription(result: Dict) -> pd.DataFrame:
    all_words = []
    for segment in result['segments']:
        for word in segment['words']:
            if 'start' not in word and 'end' not in word:
                if all_words:
                    # Merge with the previous word
                    all_words[-1]['text'] = f'{all_words[-1]["text"][:-1]}{word["word"]}"'
                else:
                    # If it's the first word, temporarily save it and wait for the next word with a timestamp
                    temp_word = word["word"]
            else:
                # Normal case, with start and end times
                word_dict = {
                    'text': f'"{temp_word}{word["word"]}"' if 'temp_word' in locals() else f'"{word["word"]}"',
                    'start': word.get('start', all_words[-1]['end'] if all_words else 0),
                    'end': word['end'],
                    'score': word.get('score', 0)
                }
                all_words.append(word_dict)
                if 'temp_word' in locals():
                    del temp_word
    
    return pd.DataFrame(all_words)

def save_results(df: pd.DataFrame):
    os.makedirs('output/log', exist_ok=True)
    excel_path = os.path.join('output/log', "cleaned_chunks.xlsx")
    df['text'] = df['text'].apply(lambda x: f'"{x}"')
    df.to_excel(excel_path, index=False)
    print(f"📊 Excel file saved to {excel_path}")

def save_language(language: str):
    os.makedirs('output/log', exist_ok=True)
    with open('output/log/transcript_language.json', 'w', encoding='utf-8') as f:
        json.dump({"language": language}, f, ensure_ascii=False, indent=4)
    
def transcribe(video_file: str):
    if not os.path.exists("output/log/cleaned_chunks.xlsx"):
        audio_file = convert_video_to_audio(video_file)
        
        if os.path.getsize(audio_file) > 25 * 1024 * 1024:
            print("⚠️ File size exceeds 25MB. Please use a smaller file.")
            return
        
        audio_base64 = encode_file_to_base64(audio_file)
        result = transcribe_audio(audio_base64)
        
        save_language(result['detected_language'])
        
        df = process_transcription(result)
        save_results(df)
    else:
        print("📊 Transcription results already exist, skipping transcription step.")

if __name__ == "__main__":
    from core.step1_ytdlp import find_video_files
    video_file = find_video_files()
    print(f"🎬 Found video file: {video_file}, starting transcription...")
    transcribe(video_file)
