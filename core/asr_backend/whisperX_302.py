import os
import io
import json
import time
import requests
from core.asr_backend.audio_preprocess import audio_slice_wav
from rich import print as rprint
from core.utils import *
from core.utils.models import *

OUTPUT_LOG_DIR = "output/log"
def transcribe_audio_302(raw_audio_path: str, vocal_audio_path: str, start: float = None, end: float = None):
        
    WHISPER_LANGUAGE = load_key("whisper.language")
    update_key("whisper.language", WHISPER_LANGUAGE)
    url = "https://api.302.ai/302/whisperx"
    
    audio_buffer = io.BytesIO(audio_slice_wav(vocal_audio_path, start, end))
    
    files = [('audio_input', ('audio_slice.wav', audio_buffer, 'application/octet-stream'))]
    payload = {"processing_type": "align", "language": WHISPER_LANGUAGE, "output": "raw"}
    
    start_time = time.time()
    rprint(f"[cyan]🎤 Transcribing audio with language:  <{WHISPER_LANGUAGE}> ...[/cyan]")
    headers = {'Authorization': f'Bearer {load_key("whisper.whisperX_302_api_key")}'}
    response = requests.request("POST", url, headers=headers, data=payload, files=files)
    
    response_json = response.json()
    
    if start is not None:
        for segment in response_json['segments']:
            segment['start'] += start
            segment['end'] += start
            for word in segment.get('words', []):
                if 'start' in word:
                    word['start'] += start
                if 'end' in word:
                    word['end'] += start
    
    
    elapsed_time = time.time() - start_time
    rprint(f"[green]✓ Transcription completed in {elapsed_time:.2f} seconds[/green]")
    return response_json

if __name__ == "__main__":  
    result = transcribe_audio_302(_RAW_AUDIO_FILE, _RAW_AUDIO_FILE)
    rprint(result)
