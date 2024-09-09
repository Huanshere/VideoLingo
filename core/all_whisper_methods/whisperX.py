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
        print(f"🎬➡️🎵 正在转换为音频......")
        subprocess.run(ffmpeg_cmd, check=True, stderr=subprocess.PIPE)
        print(f"🎬➡️🎵 已将 <{input_file}> 转换为 <{audio_file}>\n")
    
    return audio_file

def encode_file_to_base64(file_path: str) -> str:
    print("🔄 正在将音频文件编码为base64...")
    with open(file_path, 'rb') as file:
        encoded = base64.b64encode(file.read()).decode('utf-8')
        print("✅ 文件已成功编码为base64")
        return encoded

def transcribe_audio(audio_file: str) -> Dict:
    from config import WHISPER_LANGUAGE
    device = "cuda" if torch.cuda.is_available() else "cpu"
    batch_size = 16  # 如果 GPU 内存不足，请减小此值
    compute_type = "float16"  # 如果 GPU 内存不足，请改为 "int8"（可能会降低准确性）
    print(f"🚀 正在启动WhisperX... 请耐心等待...")
    try:
        whisperx_model_dir = os.path.join(MODEL_DIR, "whisperx")
        model = whisperx.load_model("large-v2", device, compute_type=compute_type, download_root=whisperx_model_dir)

        audio = whisperx.load_audio(audio_file)
        result = model.transcribe(audio, batch_size=batch_size, language=(None if WHISPER_LANGUAGE == 'auto' else WHISPER_LANGUAGE))
        # 释放 GPU 资源
        del model
        torch.cuda.empty_cache()
        
        # 保存语言信息
        save_language(result['language'])

        # 对齐 whisper 输出
        model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
        result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)

        # 再次释放 GPU 资源
        del model_a
        torch.cuda.empty_cache()

        return result
    except Exception as e:
        raise Exception(f"WhisperX 处理错误: {e}")

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
    print(f"📊 Excel文件已保存到 {excel_path}")

def save_language(language: str):
    os.makedirs('output/log', exist_ok=True)
    with open('output/log/transcript_language.json', 'w', encoding='utf-8') as f:
        json.dump({"language": language}, f, ensure_ascii=False, indent=4)

def transcribe(video_file: str):
    if not os.path.exists("output/log/cleaned_chunks.xlsx"):
        audio_file = convert_video_to_audio(video_file)
        
        if os.path.getsize(audio_file) > 25 * 1024 * 1024:
            print("⚠️ 文件大小超过25MB。请使用更小的文件。")
            return
        
        result = transcribe_audio(audio_file)
        
        df = process_transcription(result)
        save_results(df)
    else:
        print("📊 转录结果已存在，跳过转录步骤。")

if __name__ == "__main__":
    from core.step1_ytdlp import find_video_files
    video_file = find_video_files()
    print(f"🎬 找到的视频文件: {video_file}, 开始转录...")
    transcribe(video_file)
