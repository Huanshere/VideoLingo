from pathlib import Path
import json
import requests
from rich import print as rprint
import os, sys
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