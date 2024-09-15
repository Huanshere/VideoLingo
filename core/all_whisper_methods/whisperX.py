import os
import sys
import whisperx
import torch
import pandas as pd
import json
from typing import Dict

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import MODEL_DIR
from core.all_whisper_methods.whisperXapi import process_transcription, convert_video_to_audio

def transcribe_audio(audio_file: str) -> Dict:
    from config import WHISPER_LANGUAGE
    device = "cuda" if torch.cuda.is_available() else "cpu"
    batch_size = 16  # TODO Reduce this value if GPU memory is insufficient
    compute_type = "float16"  # TODO Change to "int8" if GPU memory is insufficient (may reduce accuracy)
    print(f"🚀 Starting WhisperX... Please wait patiently...")
    try:
        whisperx_model_dir = os.path.join(MODEL_DIR, "whisperx")
        model = whisperx.load_model("large-v2", device, compute_type=compute_type, download_root=whisperx_model_dir)

        audio = whisperx.load_audio(audio_file)
        result = model.transcribe(audio, batch_size=batch_size, language=(None if WHISPER_LANGUAGE == 'auto' else WHISPER_LANGUAGE))
        # Free GPU resources
        del model
        torch.cuda.empty_cache()
        
        # Save language information
        save_language(result['language'])

        # Align whisper output
        model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
        result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)

        # Free GPU resources again
        del model_a
        torch.cuda.empty_cache()

        return result
    except Exception as e:
        raise Exception(f"WhisperX processing error: {e}")

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
        
        result = transcribe_audio(audio_file)
        
        df = process_transcription(result)
        save_results(df)
    else:
        print("📊 Transcription results already exist, skipping transcription step.")

if __name__ == "__main__":
    from core.step1_ytdlp import find_video_files
    video_file = find_video_files()
    print(f"🎬 Found video file: {video_file}, starting transcription...")
    transcribe(video_file)
