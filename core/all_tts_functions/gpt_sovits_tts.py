from pathlib import Path
import requests
from rich import print as rprint
import os, sys
import subprocess
import socket
import time
import requests
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from core.config_utils import load_key

def check_lang(text_lang, prompt_lang):
    #TODO 可以考虑用ask gpt来判断语言
    if any(lang in text_lang.lower() for lang in ['zh', 'cn', '中文', 'chinese']):
        text_lang = 'zh'
    elif any(lang in text_lang.lower() for lang in ['英文', '英语', 'english']):
        text_lang = 'en'
    else:
        raise ValueError("Unsupported text language. Only Chinese and English are supported.")
    
    if 'en' in prompt_lang.lower():
        prompt_lang = 'en'
    elif any(lang in prompt_lang.lower() for lang in ['zh', 'cn', '中文', 'chinese']):
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
    TARGET_LANGUAGE = load_key("target_language")
    WHISPER_LANGUAGE = load_key("whisper.language")
    sovits_set = load_key("gpt_sovits")
    DUBBING_CHARACTER = sovits_set["character"]
    REFER_MODE = sovits_set["refer_mode"]

    from core.step2_whisper import get_whisper_language
    current_dir = Path.cwd()
    prompt_lang = get_whisper_language() if WHISPER_LANGUAGE == 'auto' else WHISPER_LANGUAGE
    prompt_text = task_df.loc[task_df['number'] == number, 'origin'].values[0]

    if REFER_MODE == 1:
        # Use the default reference audio from config
        _, config_path = find_and_check_config_path(DUBBING_CHARACTER)
        config_dir = config_path.parent

        # Find reference audio file
        ref_audio_files = list(config_dir.glob(f"{DUBBING_CHARACTER}_*.wav")) + list(config_dir.glob(f"{DUBBING_CHARACTER}_*.mp3"))
        if not ref_audio_files:
            raise FileNotFoundError(f"No reference audio file found for {DUBBING_CHARACTER}")
        ref_audio_path = ref_audio_files[0]

        # Extract content from filename
        content = ref_audio_path.stem.split('_', 1)[1]
        
        #! Check. Only support zh and en.
        prompt_lang = 'zh' if any('\u4e00' <= char <= '\u9fff' for char in content) else 'en'
        
        print(f"Detected language: {prompt_lang}")
        prompt_text = content
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


def find_and_check_config_path(dubbing_character):
    current_dir = Path(__file__).resolve().parent.parent.parent
    parent_dir = current_dir.parent

    # Find the GPT-SoVITS-v2 directory
    gpt_sovits_dir = next((d for d in parent_dir.iterdir() if d.is_dir() and d.name.startswith('GPT-SoVITS-v2')), None)

    if gpt_sovits_dir is None:
        raise FileNotFoundError("GPT-SoVITS-v2 directory not found in the parent directory.")

    config_path = gpt_sovits_dir / "GPT_SoVITS" / "configs" / f"{dubbing_character}.yaml"   
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")

    return gpt_sovits_dir, config_path

def start_gpt_sovits_server():
    current_dir = Path(__file__).resolve().parent.parent.parent
    # Check if port 9880 is already in use
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 9880))
    if result == 0:
        sock.close()
        return None

    sock.close()

    # Find and check config path
    gpt_sovits_dir, config_path = find_and_check_config_path(load_key("gpt_sovits.character"))

    # Change to the GPT-SoVITS-v2 directory
    os.chdir(gpt_sovits_dir)

    # Start the GPT-SoVITS server
    if sys.platform == "win32":
        cmd = [
            "runtime\\python.exe",
            "api_v2.py",
            "-a", "127.0.0.1",
            "-p", "9880",
            "-c", str(config_path)
        ]
        # Open the command in a new window on Windows
        process = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
    elif sys.platform == "darwin":  # macOS
        print("Please manually start the GPT-SoVITS server at http://127.0.0.1:9880, refer to api_v2.py.")
        while True:
            user_input = input("Have you started the server? (y/n): ").lower()
            if user_input == 'y':
                process = None
                break
            elif user_input == 'n':
                raise Exception("Please start the server before continuing.")
    else:
        raise OSError("Unsupported operating system. Only Windows and macOS are supported.")

    # Change back to the original directory
    os.chdir(current_dir)

    # Wait for the server to start (max 30 seconds)
    start_time = time.time()
    while time.time() - start_time < 50:
        try:
            time.sleep(15)
            response = requests.get('http://127.0.0.1:9880/ping')
            if response.status_code == 200:
                print("GPT-SoVITS server is ready.")
                return process
        except requests.exceptions.RequestException:
            pass

    raise Exception("GPT-SoVITS server failed to start within 50 seconds. Please check if GPT-SoVITS-v2-xxx folder is set correctly.")
