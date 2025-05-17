import os
import io
import json
import time
import requests
import librosa
import soundfile as sf
from rich import print as rprint
from core.utils import *
from core.utils.models import *

OUTPUT_LOG_DIR = "output/log"
def transcribe_audio_302(raw_audio_path, vocal_audio_path):
    os.makedirs(OUTPUT_LOG_DIR, exist_ok=True)
    LOG_FILE = f"{OUTPUT_LOG_DIR}/whisperx302_full.json"
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
        
    WHISPER_LANGUAGE = load_key("whisper.language")
    update_key("whisper.language", WHISPER_LANGUAGE)
    url = "https://api.302.ai/302/whisperx"
    
    y, sr = librosa.load(vocal_audio_path, sr=16000)
    
    audio_buffer = io.BytesIO()
    sf.write(audio_buffer, y, sr, format='WAV', subtype='PCM_16')
    audio_buffer.seek(0)
    
    files = [('audio_input', ('audio_slice.wav', audio_buffer, 'application/octet-stream'))]
    payload = {"processing_type": "diarize", "language": WHISPER_LANGUAGE, "output": "raw"}
    
    start_time = time.time()
    rprint(f"[cyan]🎤 Transcribing audio with language:  <{WHISPER_LANGUAGE}> ...[/cyan]")
    headers = {'Authorization': f'Bearer {load_key("whisper.whisperX_302_api_key")}'}
    response = requests.request("POST", url, headers=headers, data=payload, files=files)
    
    response_json = response.json()
    
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(response_json, f, indent=4, ensure_ascii=False)
    
    elapsed_time = time.time() - start_time
    rprint(f"[green]✓ Transcription completed in {elapsed_time:.2f} seconds[/green]")
    return response_json

if __name__ == "__main__":  
    result = transcribe_audio_302(_RAW_AUDIO_FILE, _RAW_AUDIO_FILE)
    rprint(result)
