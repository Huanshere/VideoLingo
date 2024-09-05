import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import subprocess
from openai import OpenAI
import pandas as pd
from typing import List, Dict
from uvr5.uvr5_for_videolingo import uvr5_for_videolingo
import librosa
import numpy as np
import json

def convert_video_to_audio(input_file: str):
    # 🎬➡️🎵 Convert video to audio
    # audio_file = os.path.splitext(input_file)[0] + '_temp.mp3'
    os.makedirs('output/audio', exist_ok=True)
    audio_file = 'output/audio/raw_full_audio.wav'

    if not os.path.exists(audio_file):
        # Convert video to audio using single line ffmpeg command
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

    return audio_file

def detect_background_music(audio_file: str, threshold: float = 20.0) -> bool:
    print(f"🎵➡️🔍 正在检测背景音乐...")
    y, sr = librosa.load(audio_file)
    S = np.abs(librosa.stft(y))
    contrast = librosa.feature.spectral_contrast(S=S, sr=sr)
    mean_contrast = np.mean(contrast)
    
    print(f"平均频谱对比度: {mean_contrast}")
    return mean_contrast > threshold

def uvr5_process(audio_file: str):
    audio_dir = os.path.dirname(audio_file)
    audio_name = os.path.basename(audio_file)
    vocal_file = os.path.join(audio_dir, 'raw_vocal_uvr.wav')
    bg_file = os.path.join(audio_dir, 'raw_background_uvr.wav')
    comp_vocal = os.path.join(audio_dir, 'raw_vocal.mp3')
    comp_bg = os.path.join(audio_dir, 'raw_background.mp3')

    if not os.path.exists(comp_vocal) or not os.path.exists(comp_bg):
        if not os.path.exists(vocal_file) and detect_background_music(audio_file):
            print("🎵➡️🎵 正在使用uvr5分离人声和伴奏......")
            uvr5_for_videolingo(audio_file, save_dir=audio_dir)
            os.rename(os.path.join(audio_dir, f'vocal_{audio_name}_10.wav'), vocal_file)
            os.rename(os.path.join(audio_dir, f'instrument_{audio_name}_10.wav'), bg_file)
        else:
            print("未检测到明显的背景音乐或已处理，跳过UVR处理。")
            return audio_file

        for in_file, out_file, type_name in [
            (vocal_file, comp_vocal, "人声"),
            (bg_file, comp_bg, "背景")
        ]:
            print(f"🎵➡️🗜️ 正在压缩{type_name}音频文件......")
            subprocess.run([
                'ffmpeg',
                '-i', in_file,
                '-ar', '16000',
                '-b:a', '64k',
                out_file
            ], check=True, stderr=subprocess.PIPE)
            print(f"🎵➡️🗜️ {type_name}音频文件已压缩: {out_file}")
            # 删除原始文件
            os.remove(in_file)
    else:
        print("🎵➡️🎵 UVR处理和压缩已完成，跳过处理。")

    return comp_vocal

def transcribe_audio(audio_file: str):
    from config import WHISPER_API_KEY, BASE_URL
    print(f"🎵➡️📝 正在转录音频{audio_file}为文本......")
    client = OpenAI(
        base_url=BASE_URL+"/v1",
        api_key=WHISPER_API_KEY
    )

    audio = open(audio_file, "rb")
    transcript = client.audio.transcriptions.create(
        file=audio,
        model="whisper-1",
        response_format="verbose_json",
        timestamp_granularities=["word"],
    )

    # 保存原始转录文本
    os.makedirs('output/log', exist_ok=True)
    with open("output/log/raw_transcript.txt", "w", encoding='utf-8') as f:
        f.write(transcript.text)

    print(f"🎵➡️📝 转录音频为文本完成，识别语言为: {transcript.language}")
    with open("output/log/transcript_language.json", "w", encoding='utf-8') as f:
        json.dump({"language": transcript.language}, f)

    # 处理转录结果
    all_words: List[Dict[str, float]] = [
        {'text': f'"{word_info["word"]}"', 'start': round(word_info['start'], 2), 'end': round(word_info['end'], 2)}
        for word_info in transcript.words
    ]

    df = pd.DataFrame(all_words)

    # 💾 将转录结果保存为Excel文件
    excel_path = os.path.join('output/log', "cleaned_chunks.xlsx")
    df.to_excel(excel_path, index=False)
    print(f"📊 Excel文件已保存到 {excel_path}")

    return df

def get_whisper_language():
    try:
        with open("output/log/transcript_language.json", "r", encoding='utf-8') as f:
            language = json.load(f)["language"]
        return language
    except:
        print("无法读取语言信息")
        return None

def transcribe(video_file: str):
    if not os.path.exists("output/log/cleaned_chunks.xlsx"):
        # 🎥➡️🎵 将视频转换为音频
        audio_file = convert_video_to_audio(video_file)
        if audio_file:
            #! 暂时保留， uvr5 效果一次不够感觉
            # vocal_file = uvr5_process(audio_file)
            # 🎵➡️📝 转录音频为文本并保存结果
            # transcribe_audio(vocal_file)
            transcribe_audio(audio_file)
    else:
        print("📊 转录结果已存在,跳过转录步骤。")

if __name__ == "__main__":
    from core.step1_ytdlp import find_video_files
    video_file = find_video_files()
    transcribe(video_file)