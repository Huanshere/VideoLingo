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
from core.all_whisper_methods.whisperX_utils import get_audio_duration
import hashlib
from rich import print as rprint

API_URL_SPEECH = "https://api.siliconflow.cn/v1/audio/speech"
API_URL_VOICE = "https://api.siliconflow.cn/v1/uploads/audio/voice"

AUDIO_REFERS_DIR = "output/audio/refers"
MODEL_NAME = "fishaudio/fish-speech-1.4"

def _get_headers():
    return {"Authorization": f'Bearer {load_key("sf_fish_tts.api_key")}', "Content-Type": "application/json"}

def siliconflow_fish_tts(text, save_path, mode="preset", voice_id=None, ref_audio=None, ref_text=None, check_duration=False):
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
        
        if check_duration:
            duration = get_audio_duration(wav_file_path)
            rprint(f"[blue]音频时长：{duration:.2f}秒")
            
        rprint(f"[green]成功生成语音文件：{wav_file_path}")
        return True
        
    error_msg = response.json()
    rprint(f"[red]生成语音失败：HTTP {response.status_code} | 错误详情：{error_msg}")
    return False

def create_custom_voice(audio_path, text, custom_name=None):
    if not Path(audio_path).exists():
        raise FileNotFoundError(f"Audio file not found at {audio_path}")
    
    try:
        audio_base64 = f"data:audio/wav;base64,{base64.b64encode(open(audio_path, 'rb').read()).decode('utf-8')}"
    except Exception as e:
        rprint(f"[red]Error reading file: {str(e)}")
        raise
    
    payload = {
        "audio": audio_base64,
        "model": MODEL_NAME,
        "customName": custom_name or str(uuid.uuid4())[:8],
        "text": text
    }
    
    response = requests.post(API_URL_VOICE, json=payload, headers=_get_headers())
    response_json = response.json()
    
    if response.status_code == 200:
        rprint(f"[green]Successfully created custom voice 🎙️ Voice ID: {response_json.get('uri')}")
        return response_json.get('uri')
    raise ValueError(f"Failed to create custom voice 🚫 HTTP {response.status_code}, Error details: {response_json}")

def merge_audio(files: List[str], output: str) -> bool:
    """合并音频文件，添加短暂静音，并重新编码"""
    temp_output = output + ".temp.wav"
    
    # 准备输入文件和静音源
    inputs = sum([['-i', f] for f in files], []) + ['-f', 'lavfi', '-i', 'anullsrc=duration=0.1']
    
    # 合并音频
    if subprocess.run(['ffmpeg', '-y'] + inputs + [
        '-filter_complex', f'[0:a][{len(files)}:a][1:a]concat=n=3:v=0:a=1[merged]',
        '-map', '[merged]', temp_output
    ], capture_output=True).returncode != 0:
        rprint(f"[red]合并音频失败")
        return False
    
    # 重新编码
    success = subprocess.run([
        'ffmpeg', '-y', '-i', temp_output,
        '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '1', output
    ], capture_output=True).returncode == 0
    
    try: os.remove(temp_output)
    except: pass
    
    if not success or os.path.getsize(output) == 0:
        rprint(f"[red]{'重新编码失败' if not success else '输出文件大小为0'}")
        return False
        
    return True

def get_ref_audio(task_df) -> Tuple[str, str]:
    """获取参考音频和文本，确保合并后的文本长度不超过100个字符"""
    duration = 0
    selected = []
    combined_text = ""
    
    for _, row in task_df.iterrows():
        new_text = combined_text + " " + row['origin'] if combined_text else row['origin']
        if len(new_text) > 100:
            break
            
        selected.append(row)
        combined_text = new_text
        duration += row['duration']
        if duration > 10:
            break
    
    audio_files = [f"{AUDIO_REFERS_DIR}/{row['number']}.wav" for row in selected]
    rprint(f"[yellow]Debug - Audio files to merge: {audio_files}")
    
    combined_audio = f"{AUDIO_REFERS_DIR}/combined_reference.wav"
    success = merge_audio(audio_files, combined_audio)
    
    if not success:
        rprint(f"[red]Error: Failed to merge audio files")
        return None, None
        
    rprint(f"[green]Successfully created combined audio: {combined_audio}")
    rprint(f"[green]Combined text: {combined_text} | Length: {len(combined_text)}")
    
    return combined_audio, combined_text

def siliconflow_fish_tts_for_videolingo(text, save_as, number, task_df):
    sf_fish_set = load_key("sf_fish_tts")
    MODE = sf_fish_set["mode"]

    if MODE == "preset":
        return siliconflow_fish_tts(text, save_as, mode="preset")
    elif MODE == "custom":
        video_file = find_video_files()
        custom_name = hashlib.md5(video_file.encode()).hexdigest()[:8]
        rprint(f"[yellow]Using custom name: {custom_name}")
        log_name = load_key("sf_fish_tts.custom_name")
        
        if log_name != custom_name:
            # 获取合并后的参考音频和文本
            ref_audio, ref_text = get_ref_audio(task_df)
            if ref_audio is None or ref_text is None:
                rprint(f"[red]Failed to get reference audio and text, falling back to preset mode")
                return siliconflow_fish_tts(text, save_as, mode="preset")
                
            voice_id = create_custom_voice(ref_audio, ref_text, custom_name)
            update_key("sf_fish_tts.voice_id", voice_id)
            update_key("sf_fish_tts.custom_name", custom_name)
        else:
            voice_id = load_key("sf_fish_tts.voice_id")
        return siliconflow_fish_tts(text=text, save_path=save_as, mode="custom", voice_id=voice_id)
    elif MODE == "dynamic":
        ref_audio_path = f"{AUDIO_REFERS_DIR}/{number}.wav"
        if not Path(ref_audio_path).exists():
            rprint(f"[red]Reference audio not found: {ref_audio_path}, falling back to preset mode")
            return siliconflow_fish_tts(text, save_as, mode="preset")
            
        ref_text = task_df[task_df['number'] == number]['origin'].iloc[0]
        return siliconflow_fish_tts(text=text, save_path=save_as, mode="dynamic", ref_audio=str(ref_audio_path), ref_text=ref_text)
    else:
        raise ValueError("Invalid mode. Choose 'preset', 'custom', or 'dynamic'")

if __name__ == '__main__':
    pass
    # create_custom_voice("output/audio/refers/1.wav", "Okay folks, welcome back. This is price action model number four, position trading.")
    siliconflow_fish_tts("가을 나뭇잎이 부드럽게 떨어지는 생생한 색깔을 주목하지 않을 수 없었다", "preset_test.wav", mode="preset", check_duration=True)
    # siliconflow_fish_tts("使用客制化音色测试", "custom_test.wav", mode="custom", voice_id="speech:your-voice-name:cm04pf7az00061413w7kz5qxs:mjtkgbyuunvtybnsvbxd")
    # siliconflow_fish_tts("使用动态音色测试", "dynamic_test.wav", mode="dynamic", ref_audio="output/audio/refers/1.wav", ref_text="Okay folks, welcome back. This is price action model number four, position trading.")