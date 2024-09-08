import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json

def get_whisper_language():
    try:
        with open("output/log/transcript_language.json", "r", encoding='utf-8') as f:
            language = json.load(f)["language"]
        return language
    except:
        print("无法读取语言信息")
        return None

def transcribe(video_file: str):
    from config import WHISPER_METHOD
    if WHISPER_METHOD == 'whisperx':
        from core.all_whisper_methos.whisperX import transcribe as ts
    elif WHISPER_METHOD == 'whisperxapi':
        from core.all_whisper_methos.whisperXapi import transcribe as ts
    elif WHISPER_METHOD == 'whisper_timestamped':
        from core.all_whisper_methos.whisper_timestamped import transcribe as ts
    ts(video_file)

if __name__ == "__main__":
    from core.step1_ytdlp import find_video_files
    video_file = find_video_files()
    print(f"🎬 找到的视频文件: {video_file}, 开始转录...")
    transcribe(video_file)
