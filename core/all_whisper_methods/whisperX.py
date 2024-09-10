import os
import sys
import whisperx
import torch
import pandas as pd
import json
from typing import Dict
import subprocess
import base64

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import MODEL_DIR

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

def process_transcription(result: Dict) -> pd.DataFrame:
    all_words = []
    for segment in result['segments']:
        for i, word in enumerate(segment['words']):
            if 'start' not in word and i > 0:
                all_words[-1]['text'] = f'{all_words[-1]["text"][:-1]}{word["word"]}"'
            else:
                word_dict = {
                    'text': f'{word["word"]}',
                    'start': word.get('start', all_words[-1]['end'] if all_words else 0),
                    'end': word['end'],
                    'score': word.get('score', 0)
                }
                all_words.append(word_dict)
    
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
