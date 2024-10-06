# * Settings marked with * are advanced settings that won't appear in the Streamlit page and can only be modified manually in config.py
## ======================== Basic Settings ======================== ##
# API settings
API_KEY = 'YOUR_API_KEY'
BASE_URL = 'https://yunwu.zeabur.app'
MODEL = 'claude-3-5-sonnet-20240620'

# Replicate API settings
REPLICATE_API_TOKEN = 'YOUR_TOKEN'

# * HTTP proxy settings
USE_HTTP_PROXY = False
HTTP_PROXY = "http://127.0.0.1:7890"

# Language settings, written into the prompt, can be described in natural language
TARGET_LANGUAGE = 'Simplified Chinese'

## Subtitle settings
# *Maximum length of each subtitle line in characters
MAX_SUB_LENGTH = 70
# *Translated subtitles are slightly larger than source subtitles, affecting the reference length for subtitle splitting
TARGET_SUB_MULTIPLIER = 1.1

# Video resolution [0x0, 640x360, 1920x1080]  0x0 will generate a 0-second black video placeholder
RESOLUTION = '640x360'

# Web display language, auto for automatic detection based on system [zh_CN, en_US, auto]
DISPLAY_LANGUAGE = 'auto'

## ======================== Advanced Settings ======================== ##
# *Default resolution for downloading YouTube videos [360, 1080, best]
YTB_RESOLUTION = '1080'

# Whisper settings [whisperx, whisperxapi]
WHISPER_METHOD = 'whisperx'

# Whether to perform UVR processing before transcription
UVR_BEFORE_TRANSCRIPTION = False

# Whisper specified recognition language [en, zh, auto] auto for automatic detection, en for forced translation to English
WHISPER_LANGUAGE = 'en'

# Number of LLM multi-threaded accesses
MAX_WORKERS = 8

# Maximum number of words for the first rough cut, below 18 will cut too finely affecting translation, above 22 is too long and will make subsequent subtitle splitting difficult to align
MAX_SPLIT_LENGTH = 20

# Whether to pause after extracting professional terms and before translation, allowing users to manually adjust the terminology table output\log\terminology.json
PAUSE_BEFORE_TRANSLATE = False

## ======================== Dubbing Settings ======================== ##
# TTS selection [openai, gpt_sovits, azure_tts, fish_tts]
TTS_METHOD = 'azure_tts'

# OpenAI TTS-1 API configuration
OAI_VOICE = 'alloy'
OAI_TTS_API_KEY = 'YOUR_API_KEY'
OAI_TTS_API_BASE_URL = 'https://yunwu.zeabur.app'

# Azure configuration
# Try voices online: https://speech.microsoft.com/portal/voicegallery
AZURE_KEY = 'YOUR_AZURE_KEY'
AZURE_REGION = 'eastasia'
AZURE_VOICE = 'zh-CN-YunfengNeural'

# SoVITS character configuration
DUBBING_CHARACTER = 'Huanyuv2'
# SoVits reference audio mode
REFER_MODE = 3

# FishTTS API
FISH_TTS_API_KEY = 'YOUR_FISH_TTS_API_KEY'
# FishTTS character (ensure it exists below)
FISH_TTS_CHARACTER = '丁真'
# *FishTTS character list "Character Name" : "Character ID"
FISH_TTS_CHARACTER_ID_DICT = {
    'AD学姐': '7f92f8afb8ec43bf81429cc1c9199cb1',
    '丁真': '54a5170264694bfc8e9ad98df7bd89c3',
    '赛马娘': '0eb38bc974e1459facca38b359e13511',
    '蔡徐坤': 'e4642e5edccd4d9ab61a69e82d4f8a14',
    '雷军': '738d0cc1a3e9430a9de2b544a466a7fc',
}

# Audio speed range
MIN_SPEED_FACTOR = 1
MAX_SPEED_FACTOR = 1.4
NORMAL_SPEED_FACTOR = 1.2 # Considered normal speech rate

# Merge audio configuration when generating dubbing tasks, recommended to be slightly larger than the number below
MIN_SUBTITLE_DURATION = 3
# Only trim subtitles longer than X after translation
MIN_TRIM_DURATION = 2.50

# Original voice volume in dubbed video 0.1=10% or 0
ORIGINAL_VOLUME = 0.1
# Dubbed audio volume 1.5=150%, most original dubbing audio is relatively quiet
DUB_VOLUME = 1.5

## ======================== Additional settings, please do not modify ======================== ##
# Whisper model directory
MODEL_DIR = "./_model_cache"

# Supported upload video formats
ALLOWED_VIDEO_FORMATS = ['mp4', 'mov', 'avi', 'mkv', 'flv', 'wmv', 'webm']

# LLMs that support returning JSON format, not important
llm_support_json = ['deepseek-coder', 'gpt-4o']

# Spacy models
SPACY_MODEL_MAP = {
    "en": "en_core_web_md",
    "ru": "ru_core_news_md",
    "fr": "fr_core_news_md",
    "ja": "ja_core_news_md",
    "es": "es_core_news_md",
    "de": "de_core_news_md",
    "it": "it_core_news_md",
    "zh": "zh_core_web_md",
}

# Languages that use space as separator
LANGUAGE_SPLIT_WITH_SPACE = ['en', 'es', 'fr', 'de', 'it', 'pt', 'nl', 'el', 'ru', 'ar', 'hi', 'pl', 'uk', 'vi', 'tr', 'ro', 'da', 'fi', 'hu', 'nb', 'sv']
# Languages that do not use space as separator
LANGUAGE_SPLIT_WITHOUT_SPACE = ['zh', 'ja', 'th', 'ko']

def get_joiner(language):
    if language in LANGUAGE_SPLIT_WITH_SPACE:
        return " "
    elif language in LANGUAGE_SPLIT_WITHOUT_SPACE:
        return ""
    else:
        raise ValueError(f"Unsupported language code: {language}")

import re
def get_config_value(key):
    with open('config.py', 'r', encoding='utf-8') as f:
        content = f.read()
    pattern = rf"^{re.escape(key)}\s*=\s*(.*)$"
    match = re.search(pattern, content, flags=re.MULTILINE)
    if match:
        return eval(match.group(1))
    else:
        return None