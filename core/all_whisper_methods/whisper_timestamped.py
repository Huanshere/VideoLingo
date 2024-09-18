import os,sys

from core.all_whisper_methods.whisperXapi import convert_video_to_audio

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import subprocess
import whisper_timestamped as whisper
import torch
import pandas as pd
from typing import List, Dict
import warnings
warnings.filterwarnings("ignore")
import json

def convert_video_to_audio_and_transcribe(input_file: str):
    from config import WHISPER_MODEL, MODEL_DIR, WHISPER_LANGUAGE
    # 🎬➡️🎵➡️📊 Convert video to audio and transcribe
    audio_file = convert_video_to_audio(input_file)

    # Check file size
    if os.path.getsize(audio_file) > 25 * 1024 * 1024:
        print("⚠️ Warning: File size exceeds 25MB. Please use a smaller file.")
        return None
    
    # Transcribe audio
    device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    print(f"🚀 Starting Whisper...\n🖥️ ASR device: {device}")
    print("⏳ This step will take a long time, especially after reaching 100%...")
    
    audio = whisper.load_audio(audio_file)
    os.makedirs(MODEL_DIR, exist_ok=True)
    model = whisper.load_model(WHISPER_MODEL, device=device, download_root=MODEL_DIR)
    
    transcribe_params = {'model': model, 'audio': audio, 'beam_size': 3, 'best_of': 3, 'temperature': (0.0, 0.4, 0.8)}
    if WHISPER_LANGUAGE != 'auto':
        transcribe_params['language'] = WHISPER_LANGUAGE
    result = whisper.transcribe(**transcribe_params)
    
    os.makedirs('output/log', exist_ok=True)
    with open('output/log/transcript_language.json', 'w', encoding='utf-8') as f:
        json.dump({"language": result['language']}, f, ensure_ascii=False, indent=4)
    print(f"📝 Detected language saved to output/log/transcript_language.json")

    # Process transcription results
    all_words: List[Dict[str, float]] = [
        {'text': f"{word['text']}", 'start': word['start'], 'end': word['end']}
        for segment in result['segments']
        for word in segment['words']
    ]
    
    df = pd.DataFrame(all_words)
    return df

def save_results(df: pd.DataFrame):
    # 💾 Save transcription results as Excel and text files
    os.makedirs('output', exist_ok=True)
    os.makedirs('output/log', exist_ok=True)
    excel_path = os.path.join('output/log', "cleaned_chunks.xlsx")
    # Add quotes to df[text] column to prevent Excel from auto-converting numbers
    df['text'] = df['text'].apply(lambda x: f'"{x}"')
    df.to_excel(excel_path, index=False)
    print(f"📊 Excel file saved to {excel_path}")

def transcribe(video_file: StopIteration):
    if not os.path.exists("output/log/cleaned_chunks.xlsx"):
        # 🎥➡️📝 Transcribe video to text
        df = convert_video_to_audio_and_transcribe(video_file)
        if df is not None:
            save_results(df)
    else:
        print("📊 Transcription results already exist, skipping transcription step.")

if __name__ == "__main__":
    from core.step1_ytdlp import find_video_files
    video_file = find_video_files()
    print(f"🎬 Found video file: {video_file}, starting transcription...")
    transcribe(video_file)