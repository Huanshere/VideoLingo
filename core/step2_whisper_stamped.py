import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    # audio_file = os.path.splitext(input_file)[0] + '_temp.mp3'
    os.makedirs('output/audio', exist_ok=True)
    audio_file = 'output/audio/raw_full_audio.wav'
    
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
        print(f"🎬➡️🎵 正在转换为音频......")
        subprocess.run(ffmpeg_cmd, check=True, stderr=subprocess.PIPE)
        print(f"🎬➡️🎵 已将 <{input_file}> 转换为 <{audio_file}>\n")
    
    # Check file size
    if os.path.getsize(audio_file) > 25 * 1024 * 1024:
        print("⚠️ 文件大小超过25MB。请使用更小的文件。")
        return None
    
    # Transcribe audio
    device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    print(f"🚀 正在启动Whisper...\n🖥️  ASR设备: {device}")
    print("此步骤会花费很长时间，尤其会在100%后仍然处理很长时间...")
    
    audio = whisper.load_audio(audio_file)
    os.makedirs(MODEL_DIR, exist_ok=True)
    model = whisper.load_model(WHISPER_MODEL, device=device, download_root=MODEL_DIR)
    if WHISPER_LANGUAGE == 'auto':
        # result = whisper.transcribe(model, audio, beam_size=5, best_of=5, detect_disfluencies=True, vad=True, temperature=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0))
        result = whisper.transcribe(model, audio, beam_size=5, best_of=5, temperature=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0))
    else:
        result = whisper.transcribe(model, audio, beam_size=5, best_of=5, temperature=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0), language=WHISPER_LANGUAGE)
    
    # 将 result['language'] 保存到 output\log\transcript_language.json，格式如 {"language": "japanese"}
    os.makedirs('output/log', exist_ok=True)
    with open('output/log/transcript_language.json', 'w', encoding='utf-8') as f:
        json.dump({"language": result['language']}, f, ensure_ascii=False, indent=4)
    print(f"📝 已将识别到的语言保存到 output/log/transcript_language.json")

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
    # 给df[text]列都加上""，防止数字被excel自动转换为数字
    df['text'] = df['text'].apply(lambda x: f'"{x}"')
    df.to_excel(excel_path, index=False)
    print(f"📊 Excel文件已保存到 {excel_path}")

def get_whisper_language():
    try:
        with open("output/log/transcript_language.json", "r", encoding='utf-8') as f:
            language = json.load(f)["language"]
        return language
    except:
        print("无法读取语言信息")
        return None

def transcribe(video_file: StopIteration):
    if not os.path.exists("output/log/cleaned_chunks.xlsx"):
        # 🎥➡️📝 Transcribe video to text
        df = convert_video_to_audio_and_transcribe(video_file)
        if df is not None:
            save_results(df)
    else:
        print("📊 转录结果已存在，跳过转录步骤。")

if __name__ == "__main__":
    from core.step1_ytdlp import find_video_files
    video_file = find_video_files()
    print(f"🎬 找到的视频文件: {video_file}, 开始转录...")
    transcribe(video_file)