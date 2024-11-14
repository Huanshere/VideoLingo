import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from core.all_tts_functions.gpt_sovits_tts import gpt_sovits_tts_for_videolingo
from core.all_tts_functions.siliconflow_fish_tts import siliconflow_fish_tts_for_videolingo
from core.all_tts_functions.openai_tts import openai_tts
from core.all_tts_functions.fish_tts import fish_tts
from core.all_tts_functions.azure_tts import azure_tts
from core.config_utils import load_key
from rich import print as rprint
import re
from pydub import AudioSegment

def tts_main(text, save_as, number, task_df):
    # 检查文本是否为空（去除标点符号和空白字符后）
    cleaned_text = re.sub(r'[^\w\s]', '', text).strip()
    if not cleaned_text:
        silence = AudioSegment.silent(duration=100)  # 100ms = 0.1s
        silence.export(save_as, format="wav")
        rprint(f"Created silent audio for empty text: {save_as}")
        return
    
    # 如果文件存在，跳过
    if os.path.exists(save_as):
        return
    
    print(f"Generating <{text}...>")
    TTS_METHOD = load_key("tts_method")
    if TTS_METHOD == 'openai_tts':
        openai_tts(text, save_as)
    elif TTS_METHOD == 'gpt_sovits':
        #! 注意 gpt_sovits_tts 只支持输出中文，输入中文或英文
        gpt_sovits_tts_for_videolingo(text, save_as, number, task_df)
    elif TTS_METHOD == 'fish_tts':
        fish_tts(text, save_as)
    elif TTS_METHOD == 'azure_tts':
        azure_tts(text, save_as)
    elif TTS_METHOD == 'sf_fish_tts':
        siliconflow_fish_tts_for_videolingo(text, save_as, number, task_df)