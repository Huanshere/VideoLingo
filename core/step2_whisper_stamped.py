import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import subprocess
import whisper_timestamped as whisper
import torch
import pandas as pd
from typing import List, Dict
import warnings
warnings.filterwarnings("ignore")
from config import WHISPER_MODEL
MODEL_DIR = "./_model_cache"

def convert_video_to_audio_and_transcribe(input_file: str):
    # 🎬➡️🎵➡️📊 Convert video to audio and transcribe
    audio_file = os.path.splitext(input_file)[0] + '_temp.mp3'
    
    try:
        if not os.path.exists(audio_file):
            # Convert video to audio
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
        
        # Check file size
        if os.path.getsize(audio_file) > 25 * 1024 * 1024:
            print("⚠️ File size exceeds 25MB. Please use a smaller file.")
            return None
        
        # Transcribe audio
        device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
        print(f"🚀 Starting Whisper...\n🖥️  ASR Device: {device}")
        
        audio = whisper.load_audio(audio_file)
        os.makedirs(MODEL_DIR, exist_ok=True)
        model = whisper.load_model(WHISPER_MODEL, device=device, download_root=MODEL_DIR)
        result = whisper.transcribe(model, audio, language="en")
        
        # Process transcription results
        all_words: List[Dict[str, float]] = [
            {'text': f"{word['text']}", 'start': word['start'], 'end': word['end']}
            for segment in result['segments']
            for word in segment['words']
        ]
        
        df = pd.DataFrame(all_words)
        return df
    
    except subprocess.CalledProcessError as e:
        print(f"❌ Error converting {input_file}: {e.stderr.decode()}")
        return None
    finally:
        if os.path.exists(audio_file):
            os.remove(audio_file)
            print(f"🗑️ Temporary audio file {audio_file} has been deleted.")


def save_results(df: pd.DataFrame):
    # 💾 Save transcription results as Excel and text files
    os.makedirs('output', exist_ok=True)
    os.makedirs('output/log', exist_ok=True)
    excel_path = os.path.join('output/log', "cleaned_chunks.xlsx")
    # 给df[text]列都加上""，防止数字被excel自动转换为数字
    df['text'] = df['text'].apply(lambda x: f'"{x}"')
    df.to_excel(excel_path, index=False)
    print(f"📊 Excel file has been saved to {excel_path}")

def transcript(video_file: StopIteration):
    if not os.path.exists("output/log/cleaned_chunks.xlsx"):
        # 🎥➡️📝 Transcribe video to text
        df = convert_video_to_audio_and_transcribe(video_file)
        if df is not None:
            save_results(df)
    else:
        print("📊 The transcription results already exist, skipping the transcription step.")

if __name__ == "__main__":
    transcript("KUNG FU PANDA 4 ｜ Official Trailer.mp4")