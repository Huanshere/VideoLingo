from pathlib import Path
import json
import requests
from rich import print as rprint
import os, sys
import subprocess
import socket
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def check_lang(text_lang, prompt_lang):
    if any(lang in text_lang.lower() for lang in ['zh', 'cn', '中文']):
        text_lang = 'zh'
    else:
        raise ValueError("Unsupported text language. Only Chinese is supported.")
    
    if 'en' in prompt_lang.lower():
        prompt_lang = 'en'
    elif any(lang in prompt_lang.lower() for lang in ['zh', 'cn', '中文']):
        prompt_lang = 'zh'
    else:
        raise ValueError("Unsupported prompt language. Only Chinese and English are supported.")
    
    return text_lang, prompt_lang


def gpt_sovits_tts(text, text_lang, save_path, ref_audio_path, prompt_lang, prompt_text):
    text_lang, prompt_lang = check_lang(text_lang, prompt_lang)

    current_dir = Path.cwd()
    
    payload = {
        'text': text,
        'text_lang': text_lang,
        'ref_audio_path': str(ref_audio_path),
        'prompt_lang': prompt_lang,
        'prompt_text': prompt_text,
        "speed_factor": 1.0,
    }

    def save_audio(response, save_path, current_dir):
        if save_path:
            full_save_path = current_dir / save_path
            full_save_path.parent.mkdir(parents=True, exist_ok=True)
            full_save_path.write_bytes(response.content)
            rprint(f"[bold green]音频保存成功:[/bold green] {full_save_path}")
        return True

    response = requests.post('http://127.0.0.1:9880/tts', json=payload)
    if response.status_code == 200:
        return save_audio(response, save_path, current_dir)
    else:
        rprint(f"[bold red]TTS请求失败，状态码:[/bold red] {response.status_code}")
        return False
        


def gpt_sovits_tts_for_videolingo(text, save_as, number, task_df):
    start_gpt_sovits_server()
    from config import TARGET_LANGUAGE, WHISPER_LANGUAGE, REFER_MODE, DUBBING_CHARACTER
    from core.step2_whisper import get_whisper_language

    current_dir = Path.cwd()
    prompt_lang = get_whisper_language() if WHISPER_LANGUAGE == 'auto' else WHISPER_LANGUAGE
    prompt_text = task_df.loc[task_df['number'] == number, 'origin'].values[0]

    if REFER_MODE == 1:
        # Use the default reference audio from config
        model_path = current_dir / "_model_cache" / "GPT_SoVITS" / "trained" / DUBBING_CHARACTER
        config_path = model_path / "infer_config.json"
        config = json.loads(config_path.read_text(encoding='utf-8'))
        
        default_emotion = config['emotion_list']['default']
        ref_audio_path = model_path / default_emotion['ref_wav_path']
        prompt_lang = default_emotion['prompt_language']
        prompt_text = default_emotion['prompt_text']
    elif REFER_MODE == 2:
        # Use only the reference audio path
        ref_audio_path = current_dir / "output/audio/refers/1.wav"
    elif REFER_MODE == 3:
        # Use the provided reference audio path
        ref_audio_path = current_dir / f"output/audio/refers/{number}.wav"
    else:
        raise ValueError("Invalid REFER_MODE. Choose 1, 2, or 3.")

    success = gpt_sovits_tts(text, TARGET_LANGUAGE, save_as, ref_audio_path, prompt_lang, prompt_text)

    if not success and REFER_MODE == 3:
        rprint(f"[bold red]TTS请求失败，切换回模式2重试[/bold red]")
        ref_audio_path = current_dir / "output/audio/refers/1.wav"
        gpt_sovits_tts(text, TARGET_LANGUAGE, save_as, ref_audio_path, prompt_lang, prompt_text)


def start_gpt_sovits_server():
    from config import DUBBING_CHARACTER
    import time
    import requests

    # Check if port 9880 is already in use
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 9880))
    if result == 0:
        sock.close()
        return None

    sock.close()

    # Find the root directory of the current Python script
    current_dir = Path(__file__).resolve().parent.parent.parent
    parent_dir = current_dir.parent

    # Find the GPT-SoVITS-v2 directory
    gpt_sovits_dir = next((d for d in parent_dir.iterdir() if d.is_dir() and d.name.startswith('GPT-SoVITS-v2')), None)

    if gpt_sovits_dir is None:
        raise FileNotFoundError("GPT-SoVITS-v2 directory not found in the parent directory.")

    # Change to the GPT-SoVITS-v2 directory
    os.chdir(gpt_sovits_dir)
    # check f"GPT_SoVITS/configs/{DUBBING_CHARACTER}.yaml"
    config_path = gpt_sovits_dir / "GPT_SoVITS" / "configs" / f"{DUBBING_CHARACTER}.yaml"   
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")

    # Start the GPT-SoVITS server
    cmd = [
        "runtime\\python.exe",
        "api_v2.py",
        "-a", "127.0.0.1",
        "-p", "9880",
        "-c", str(config_path)
    ]

    # Open the command in a new window
    process = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)

    # Change back to the original directory
    os.chdir(current_dir)

    # Wait for the server to start (max 20 seconds)
    start_time = time.time()
    while time.time() - start_time < 20:
        try:
            response = requests.get('http://127.0.0.1:9880/ping')
            if response.status_code == 200:
                print("GPT-SoVITS server is ready.")
                return process
        except requests.exceptions.RequestException:
            time.sleep(1)

    print("GPT-SoVITS server failed to start within 20 seconds.")
    return process