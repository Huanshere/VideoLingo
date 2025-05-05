import http.client
import json
import os
import requests
from pydub import AudioSegment
from core.asr_backend.audio_preprocess import normalize_audio_volume
from core.utils import *
from core.utils.models import *

API_KEY = load_key("f5tts.302_api")
UPLOADED_REFER_URL = None

def upload_file_to_302(file_path):
    API_KEY = load_key("f5tts.302_api")
    url = "https://api.302.ai/302/upload-file"
    
    files = [('file', (os.path.basename(file_path), open(file_path, 'rb'), 'application/octet-stream'))]
    headers = {'Authorization': f'Bearer {API_KEY}'}
    
    response = requests.request("POST", url, headers=headers, data={}, files=files)
    
    if response.status_code == 200:
        response_data = response.json()
        if response_data.get('code') == 200:
            return response_data.get('data')
        return None
    return None

def _f5_tts(text: str, refer_url: str, save_path: str) -> bool:
    conn = http.client.HTTPSConnection("api.302.ai")
    payload = json.dumps({"gen_text": text, "ref_audio_url": refer_url, "model_type": "F5-TTS"})
    headers = {'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'}

    conn.request("POST", "/302/submit/f5-tts", payload, headers)
    res = conn.getresponse()
    data = json.loads(res.read().decode("utf-8"))
    
    if "audio_url" in data and "url" in data["audio_url"]:
        # Download audio file
        audio_url = data["audio_url"]["url"]
        audio_conn = http.client.HTTPSConnection("file.302.ai")
        audio_conn.request("GET", audio_url.replace("https://file.302.ai", ""))
        audio_res = audio_conn.getresponse()
        
        with open(save_path, "wb") as f: 
            f.write(audio_res.read())
        print(f"Audio file saved to {save_path}")
        return True
    
    print("Request failed:", data)
    return False

def _merge_audio(files, output: str) -> bool:
    """Merge audio files, add a brief silence"""
    try:
        # Create an empty audio segment
        combined = AudioSegment.empty()
        silence = AudioSegment.silent(duration=100)  # 100ms silence
        
        # Add audio files one by one
        for file in files:
            audio = AudioSegment.from_wav(file)
            combined += audio + silence
        combined += silence
        combined.export(output, format="wav", parameters=["-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1"])
        
        if os.path.getsize(output) == 0:
            rprint(f"[red]Output file size is 0")
            return False
            
        rprint(f"[green]Successfully merged audio files")
        return True
        
    except Exception as e:
        rprint(f"[red]Failed to merge audio: {str(e)}")
        return False
    
def _get_ref_audio(task_df, min_duration=8, max_duration=14.5) -> str:
    """Get reference audio, ensuring the combined audio duration is > min_duration and < max_duration"""
    rprint(f"[blue]🎯 Starting reference audio selection process...")
    
    duration = 0
    selected = []
    
    for _, row in task_df.iterrows():
        current_duration = row['duration']
        
        # Skip if adding this segment would exceed max duration
        if current_duration + duration > max_duration:
            continue
            
        # Add segments until we exceed min duration
        selected.append(row)
        duration += current_duration
        
        # Once we exceed min duration and are under max, we're done
        if duration > min_duration and duration < max_duration:
            break
    
    if not selected:
        rprint(f"[red]❌ No valid segments found (could not reach minimum {min_duration}s duration)")
        return None
        
    rprint(f"[blue]📊 Selected {len(selected)} segments, total duration: {duration:.2f}s")
    
    audio_files = [f"{_AUDIO_REFERS_DIR}/{row['number']}.wav" for row in selected]
    rprint(f"[yellow]🎵 Audio files to merge: {audio_files}")
    
    combined_audio = f"{_AUDIO_REFERS_DIR}/refer.wav"
    success = _merge_audio(audio_files, combined_audio)
    
    if not success:
        rprint(f"[red]❌ Error: Failed to merge audio files")
        return False
    
    rprint(f"[green]✅ Successfully created combined audio: {combined_audio}")
    
    return combined_audio

def f5_tts_for_videolingo(text: str, save_as: str, number: int, task_df):
    global UPLOADED_REFER_URL
    
    # Only process the reference audio if we haven't uploaded it yet
    if UPLOADED_REFER_URL is None:
        refer_path = _get_ref_audio(task_df)
        normalized_refer_path = normalize_audio_volume(refer_path, f"{_AUDIO_REFERS_DIR}/refer_normalized.wav")
        UPLOADED_REFER_URL = upload_file_to_302(normalized_refer_path)
        rprint(f"[green]✅ Reference audio uploaded, URL cached for reuse")
    
    try:
        success = _f5_tts(text=text, refer_url=UPLOADED_REFER_URL, save_path=save_as)
        return success
    except Exception as e:
        print(f"Error in f5_tts_for_videolingo: {str(e)}")
        return False

if __name__ == "__main__":
    test_refer_url = "https://file.302.ai/gpt/imgs/20250226/717e574dc8e440e3b6f8cb4b3acb40e0.mp3"
    test_text = "Hello, world!"
    test_save_as = "test_f5_tts.wav"
    success = _f5_tts(text=test_text, refer_url=test_refer_url, save_path=test_save_as)
    print(f"Test result: {success}")