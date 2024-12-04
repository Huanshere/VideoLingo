import os, sys
import re
from rich import print as rprint
from pydub import AudioSegment

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from core.config_utils import load_key
from core.all_whisper_methods.whisperX_utils import get_audio_duration
from core.all_tts_functions.gpt_sovits_tts import gpt_sovits_tts_for_videolingo
from core.all_tts_functions.siliconflow_fish_tts import siliconflow_fish_tts_for_videolingo
from core.all_tts_functions.openai_tts import openai_tts
from core.all_tts_functions.fish_tts import fish_tts
from core.all_tts_functions.azure_tts import azure_tts
from core.ask_gpt import ask_gpt
from core.prompts_storage import get_correct_text_prompt
from core.all_tts_functions.cosyvoice_tts import cosyvoice_tts
from core.all_tts_functions.cosyvoice_cloud import cosyvoice_cloud
from core.all_tts_functions.sambert_cloud import sambert_cloud

def clean_text_for_tts(text):
    """Remove problematic characters for TTS"""
    chars_to_remove = ['&', '®', '™', '©']
    for char in chars_to_remove:
        text = text.replace(char, '')
    return text.strip()


def tts_main(text, save_as, number, task_df):
    text = clean_text_for_tts(text)
    # 检查文本是否为空或单字符，单字符配音容易触发bug
    cleaned_text = re.sub(r'[^\w\s]', '', text).strip()
    if not cleaned_text or len(cleaned_text) <= 1:
        silence = AudioSegment.silent(duration=100)  # 100ms = 0.1s
        silence.export(save_as, format="wav")
        rprint(f"Created silent audio for empty/single-char text: {save_as}")
        return
    
    # 如果文件存在，跳过
    if os.path.exists(save_as):
        return
    
    print(f"Generating <{text}...>")
    TTS_METHOD = load_key("tts_method")

    max_retries = 3
    for attempt in range(max_retries):
        try:
            if attempt >= max_retries - 1:
                print("Asking GPT to correct text...")
                correct_text = ask_gpt(get_correct_text_prompt(text),log_title='tts_correct_text')
                text = correct_text['text']
            if TTS_METHOD == 'openai_tts':
                openai_tts(text, save_as)
            elif TTS_METHOD == 'gpt_sovits':
                gpt_sovits_tts_for_videolingo(text, save_as, number, task_df)
            elif TTS_METHOD == 'fish_tts':
                fish_tts(text, save_as)
            elif TTS_METHOD == 'azure_tts':
                azure_tts(text, save_as)
            elif TTS_METHOD == 'sf_fish_tts':
                siliconflow_fish_tts_for_videolingo(text, save_as, number, task_df)
            elif TTS_METHOD == 'cosyvoice':
                cosyvoice_tts(text, save_as)
            elif TTS_METHOD == 'cosyvoice_cloud':
                cosyvoice_cloud(text, save_as)
            elif TTS_METHOD == 'sambert':
                sambert_cloud(text, save_as)
            
            # 检查生成的音频时长
            duration = get_audio_duration(save_as)
            if duration > 0:
                break
            else:
                if os.path.exists(save_as):
                    os.remove(save_as)
                raise Exception("Generated audio duration is 0")
                
        except Exception as e:
            if attempt == max_retries - 1:
                raise Exception(f"Failed to generate audio after {max_retries} attempts: {str(e)}")
            print(f"Attempt {attempt + 1} failed, retrying...")