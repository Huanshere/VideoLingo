import requests
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.config_utils import load_key
from rich import print as rprint
import time
import json
import tempfile
import subprocess

OUTPUT_LOG_DIR = "output/log"


def transcribe_audio_302(audio_path: str, start: float = None, end: float = None, log_index: int = 0):
    os.makedirs(OUTPUT_LOG_DIR, exist_ok=True)
    LOG_FILE = f"{OUTPUT_LOG_DIR}/whisperx302_{log_index}.json"
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
        
    WHISPER_LANGUAGE = load_key("whisper.language")
    url = "https://api.302.ai/302/whisperx"
    
    # 如果指定了开始和结束时间，创建临时音频片段
    if start is not None and end is not None:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
            temp_audio_path = temp_audio.name
            
        # 使用ffmpeg截取音频片段
        ffmpeg_cmd = f'ffmpeg -y -i "{audio_path}" -ss {start} -t {end-start} -vn -ar 32000 -ac 1 "{temp_audio_path}"'
        subprocess.run(ffmpeg_cmd, shell=True, check=True, capture_output=True)
        audio_path = temp_audio_path
    
    payload = {
        "processing_type": "align",
        "language": WHISPER_LANGUAGE,
        "output": "raw"
    }
    
    start_time = time.time()
    rprint(f"[cyan]🎤 Transcribing audio with language:  <{WHISPER_LANGUAGE}> ...[/cyan]")
    files = [
        ('audio_input',(
            os.path.basename(audio_path),
            open(audio_path, 'rb'),
            'application/octet-stream'
        ))
    ]
    
    headers = {
        'Authorization': f'Bearer {load_key("whisper.whisperX_302_api_key")}'
    }

    response = requests.request("POST", url, headers=headers, data=payload, files=files)
    
    # 清理临时文件
    if start is not None and end is not None:
        if os.path.exists(temp_audio_path):
            os.unlink(temp_audio_path)
    
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(response.json(), f, indent=4, ensure_ascii=False)
        
    # 调整时间戳
    if start is not None:
        result = response.json()
        for segment in result['segments']:
            segment['start'] += start
            segment['end'] += start
            for word in segment.get('words', []):
                if 'start' in word:
                    word['start'] += start
                if 'end' in word:
                    word['end'] += start
        response._content = json.dumps(result).encode()
    
    elapsed_time = time.time() - start_time
    rprint(f"[green]✓ Transcription completed in {elapsed_time:.2f} seconds[/green]")
    return response.json()

if __name__ == "__main__":  
    # 使用示例:
    result = transcribe_audio_302("output/audio/raw.mp3")
    rprint(result)
