import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.step1_ytdlp import find_video_files
from core.config_utils import load_key

def transcribe():
    WHISPER_METHOD = load_key("whisper.method")
    video_file = find_video_files()
    if WHISPER_METHOD == 'whisperx':
        from core.all_whisper_methods.whisperX import transcribe as ts
    elif WHISPER_METHOD == 'whisperxapi':
        from core.all_whisper_methods.whisperXapi import transcribe as ts
    ts(video_file)

if __name__ == "__main__":
    transcribe()