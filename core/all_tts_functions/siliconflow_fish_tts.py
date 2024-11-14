import requests
from pathlib import Path
import os, sys
import base64
import uuid
import subprocess
from typing import List, Tuple
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from core.config_utils import load_key, update_key
from core.step1_ytdlp import find_video_files
import hashlib
from rich import print as rprint

API_URL_SPEECH = "https://api.siliconflow.cn/v1/audio/speech"
API_URL_VOICE = "https://api.siliconflow.cn/v1/uploads/audio/voice"

AUDIO_REFERS_DIR = "output/audio/refers"
MODEL_NAME = "fishaudio/fish-speech-1.4"

def _get_headers():
    return {"Authorization": f'Bearer {load_key("sf_fish_tts.api_key")}', "Content-Type": "application/json"}

def siliconflow_fish_tts(text, save_path, mode="preset", voice_id=None, ref_audio=None, ref_text=None):
    sf_fish_set, headers = load_key("sf_fish_tts"), _get_headers()
    payload = {"model": MODEL_NAME, "response_format": "wav", "stream": False, "input": text}
    
    if mode == "preset": 
        payload["voice"] = f"fishaudio/fish-speech-1.4:{sf_fish_set['voice']}"
    elif mode == "custom": 
        if not voice_id: 
            raise ValueError("custom mode requires voice_id")
        payload["voice"] = voice_id
    elif mode == "dynamic":
        if not ref_audio or not ref_text: 
            raise ValueError("dynamic mode requires ref_audio and ref_text")
        with open(ref_audio, 'rb') as f: 
            audio_base64 = base64.b64encode(f.read()).decode('utf-8')
        payload = {
            "model": MODEL_NAME,
            "response_format": "wav",
            "stream": False,
            "input": text,
            "voice": None,
            "references": [{
                "audio": f"data:audio/wav;base64,{audio_base64}",
                "text": ref_text
            }]
        }
    else: raise ValueError("Invalid mode")

    response = requests.post(API_URL_SPEECH, json=payload, headers=headers)
    if response.status_code == 200:
        wav_file_path = Path(save_path).with_suffix('.wav')
        wav_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(wav_file_path, 'wb') as f: f.write(response.content)
        rprint(f"[green]成功生成语音文件：{wav_file_path}")
        return True
    error_msg = response.json()
    rprint(f"[red]生成语音失败：HTTP {response.status_code} | 错误详情：{error_msg}")
    return False

def create_custom_voice(audio_path, text, custom_name=None):
    with open(audio_path, 'rb') as f: 
        audio_base64 = f"data:audio/mpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}"
    
    if not custom_name:
        custom_name = str(uuid.uuid4())[:8]
        
    payload = {"audio": audio_base64, "model": MODEL_NAME, "customName": custom_name, "text": text}
    
    response = requests.post(API_URL_VOICE, json=payload, headers=_get_headers())
    response_json = response.json()
    
    if response.status_code == 200:
        rprint(f"[green]Successfully created custom voice 🎙️ Voice ID: {response_json.get('uri')}")
        return response_json.get('uri')
    else:
        raise ValueError(f"Failed to create custom voice 🚫 HTTP {response.status_code}, Error details: {response_json}")

def merge_audio(files: List[str], output: str) -> bool:
    """合并音频文件，添加短暂静音"""
    inputs = []
    for file in files:
        inputs.extend(['-i', file])
    
    inputs.extend(['-f', 'lavfi', '-i', 'anullsrc=duration=0.1'])
    
    cmd = ['ffmpeg', '-y'] + inputs + [
        '-filter_complex', 
        f'[0:a][silence][1:a]concat=n=3:v=0:a=1[merged]', 
        '-map', '[merged]', 
        output
    ]
    
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0

def get_ref_audio(task_df) -> Tuple[str, str]:
    """获取参考音频和文本"""
    duration = 0
    selected = []
    
    for _, row in task_df.iterrows():
        selected.append(row)
        duration += row['duration']
        if duration > 20:
            break
    
    audio_files = [f"{AUDIO_REFERS_DIR}/{row['number']}.wav" for row in selected]
    combined_text = " ".join(row['origin'] for row in selected)
    
    combined_audio = f"{AUDIO_REFERS_DIR}/combined_reference.wav"
    merge_audio(audio_files, combined_audio)
    
    return combined_audio, combined_text

def siliconflow_fish_tts_for_videolingo(text, save_as, number, task_df):
    sf_fish_set = load_key("sf_fish_tts")
    MODE = sf_fish_set["mode"]

    if MODE == "preset":
        return siliconflow_fish_tts(text, save_as, mode="preset")
    elif MODE == "custom":
        video_file = find_video_files()
        custom_name = hashlib.md5(video_file.encode()).hexdigest()[:8]
        print(f"Using custom name: {custom_name}")
        log_name = load_key("sf_fish_tts.custom_name")
        
        if log_name != custom_name:
            # 获取合并后的参考音频和文本
            ref_audio, ref_text = get_ref_audio(task_df)
            voice_id = create_custom_voice(ref_audio, ref_text, custom_name)
            update_key("sf_fish_tts.voice_id", voice_id)
            update_key("sf_fish_tts.custom_name", custom_name)
        else:
            voice_id = load_key("sf_fish_tts.voice_id")
        return siliconflow_fish_tts(text=text, save_path=save_as, mode="custom", voice_id=voice_id)
    elif MODE == "dynamic":
        ref_audio_path = f"{AUDIO_REFERS_DIR}/{number}.wav"
        ref_text = task_df[task_df['number'] == number]['origin'].iloc[0]
        return siliconflow_fish_tts(text=text, save_path=save_as, mode="dynamic", ref_audio=str(ref_audio_path), ref_text=ref_text)
    else:
        raise ValueError("Invalid mode. Choose 'preset', 'custom', or 'dynamic'")

if __name__ == '__main__':
    pass
    # create_custom_voice("output/audio/refers/1.wav", "Okay folks, welcome back. This is price action model number four, position trading.")
    # siliconflow_fish_tts("使用预制音色测试", "preset_test.wav", mode="preset")
    # siliconflow_fish_tts("使用客制化音色测试", "custom_test.wav", mode="custom", voice_id="speech:your-voice-name:cm04pf7az00061413w7kz5qxs:mjtkgbyuunvtybnsvbxd")
    # siliconflow_fish_tts("使用动态音色测试", "dynamic_test.wav", mode="dynamic", ref_audio="output/audio/refers/1.wav", ref_text="Okay folks, welcome back. This is price action model number four, position trading.")