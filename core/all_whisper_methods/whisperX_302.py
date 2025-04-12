import requests
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.config_utils import load_key
from rich import print as rprint
import time
import json
import librosa
import soundfile as sf
import io
from core.all_whisper_methods.audio_preprocess import save_language

OUTPUT_LOG_DIR = "output/log"
def transcribe_audio_302(raw_audio_path: str, vocal_audio_path: str, start: float = None, end: float = None):
    os.makedirs(OUTPUT_LOG_DIR, exist_ok=True)
    LOG_FILE = f"{OUTPUT_LOG_DIR}/whisperx302.json"
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
        
    WHISPER_LANGUAGE = load_key("whisper.language")
    save_language(WHISPER_LANGUAGE) # since 302ai doesn't return language
    url = "https://api.302.ai/302/whisperx"
    
    # 加载音频并处理start和end参数
    y, sr = librosa.load(vocal_audio_path, sr=16000)
    audio_duration = len(y) / sr
    
    if start is None or end is None:
        start = 0
        end = audio_duration
        
    start_sample = int(start * sr)
    end_sample = int(end * sr)
    y_slice = y[start_sample:end_sample]
    
    # 将音频数据直接写入内存缓冲区
    audio_buffer = io.BytesIO()
    sf.write(audio_buffer, y_slice, sr, format='WAV', subtype='PCM_16')
    audio_buffer.seek(0)
    
    files = [
        ('audio_input', (
            'audio_slice.wav',  # 虚拟文件名
            audio_buffer,
            'application/octet-stream'
        ))
    ]

    payload = {
        "processing_type": "align",
        "language": WHISPER_LANGUAGE,
        "output": "raw"
    }
    
    start_time = time.time()
    rprint(f"[cyan]🎤 Transcribing audio with language:  <{WHISPER_LANGUAGE}> ...[/cyan]")
    headers = {'Authorization': f'Bearer {load_key("whisper.whisperX_302_api_key")}'}
    response = requests.request("POST", url, headers=headers, data=payload, files=files)
    
    response_json = response.json()
    
    # 调整时间戳
    if start is not None:
        for segment in response_json['segments']:
            segment['start'] += start
            segment['end'] += start
            for word in segment.get('words', []):
                if 'start' in word:
                    word['start'] += start
                if 'end' in word:
                    word['end'] += start
    
    # 保存调整后的结果
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(response_json, f, indent=4, ensure_ascii=False)
    
    elapsed_time = time.time() - start_time
    rprint(f"[green]✓ Transcription completed in {elapsed_time:.2f} seconds[/green]")
    return response_json

if __name__ == "__main__":  
    # 使用示例:
    result = transcribe_audio_302("output/audio/raw.mp3", "output/audio/raw.mp3")
    rprint(result)
