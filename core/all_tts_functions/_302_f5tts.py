import http.client
import json
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from core.config_utils import load_key
from rich import print as rprint
from pydub import AudioSegment
from core.all_tts_functions._302_file_upload import upload_file_to_302

API_KEY = load_key("f5tts.302_api")
AUDIO_REFERS_DIR = "output/audio/refers"

def _f5_tts(text: str, refer_url: str, save_path: str) -> bool:
    conn = http.client.HTTPSConnection("api.302.ai")
    payload = json.dumps({
        "gen_text": text,
        "ref_audio_url": refer_url,
        "model_type": "F5-TTS"
    })
    
    api_key = load_key("api_keys.302_api")
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    conn.request("POST", "/302/submit/f5-tts", payload, headers)
    res = conn.getresponse()
    data = json.loads(res.read().decode("utf-8"))
    
    if "audio_url" in data and "url" in data["audio_url"]:
        # 下载音频文件
        audio_url = data["audio_url"]["url"]
        audio_conn = http.client.HTTPSConnection("file.302.ai")
        audio_conn.request("GET", audio_url.replace("https://file.302.ai", ""))
        audio_res = audio_conn.getresponse()
        
        # 保存音频文件
        with open(save_path, "wb") as f:
            f.write(audio_res.read())
        print(f"音频文件已保存到 {save_path}")
        return True
    
    print("请求失败:", data)
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
            
        # Add final silence
        combined += silence
        
        # Export the combined file
        combined.export(output, format="wav", parameters=[
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1"
        ])
        
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
    
    audio_files = [f"{AUDIO_REFERS_DIR}/{row['number']}.wav" for row in selected]
    rprint(f"[yellow]🎵 Audio files to merge: {audio_files}")
    
    combined_audio = f"{AUDIO_REFERS_DIR}/refer.wav"
    success = _merge_audio(audio_files, combined_audio)
    
    if not success:
        rprint(f"[red]❌ Error: Failed to merge audio files")
        return False
    
    rprint(f"[green]✅ Successfully created combined audio: {combined_audio}")
    
    return combined_audio

def normalize_audio_volume(audio_path: str, output_path: str, target_db: float = -20.0):
    audio = AudioSegment.from_file(audio_path)
    change_in_dBFS = target_db - audio.dBFS
    normalized_audio = audio.apply_gain(change_in_dBFS)
    normalized_audio.export(output_path, format="wav")
    rprint(f"[green]✅ Audio normalized from {audio.dBFS:.1f}dB to {target_db:.1f}dB[/green]")
    return output_path

def f5_tts_for_videolingo(text: str, save_as: str, number: int, task_df):
    task_id = load_key("task_id")
    if not task_id:
        raise ValueError("Error: Task ID not found")
    
    dst_refer_path = f"tasks/{task_id}/refer.wav"
    refer_path = _get_ref_audio(task_df)
    normalized_refer_path = normalize_audio_volume(refer_path, f"{AUDIO_REFERS_DIR}/refer_normalized.wav")
    refer_url = upload_file_to_302(normalized_refer_path)
    try:
        success = _f5_tts(text=text, refer_url=refer_url, save_path=save_as)
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