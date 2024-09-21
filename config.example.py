# 建议在 streamlit 页面中调整设置
## ======================== 基本设置 ======================== ##

# API settings
API_KEY = 'YOUR_API_KEY'
BASE_URL = 'https://yunwu.zeabur.app'
MODEL = ['claude-3.5-sonnet-20240620']

# Replicate API 设置
REPLICATE_API_TOKEN = 'YOUR_TOKEN'

# 语言设置，用自然语言描述
TARGET_LANGUAGE = '简体中文'

# 字幕设置
# 每行字幕的最大长度字母数量
MAX_SUB_LENGTH = 75
# 输出字幕字号更大一些
TARGET_SUB_MULTIPLIER = 1.2

# 视频分辨率
# Video resolution
RESOLUTION = '640x360'

# 显示语言
# Display language
DISPLAY_LANGUAGE = 'zh_CN'

## ======================== 进阶设置设置 ======================== ##
# Whisper 设置 [whisperx, whisperxapi]
WHISPER_METHOD = 'whisperxapi'

# Whisper 指定识别语言
WHISPER_LANGUAGE = 'auto'

# 支持视频格式
ALLOWED_VIDEO_FORMATS = ['mp4', 'mov', 'avi', 'mkv', 'flv', 'wmv', 'webm']

# gpt多线程数量
MAX_WORKERS = 6

# 每一步的 LLM 模型选择
step3_2_split_model = MODEL[0]
step4_1_summarize_model = MODEL[0]
step4_2_translate_direct_model = MODEL[0]
step4_2_translate_free_model = MODEL[0]
step5_align_model = MODEL[0]
step9_trim_model = MODEL[0]

# 支持返回 JSON 格式的 LLM，不重要
llm_support_json = ['deepseek-coder']

# Whisper 模型目录
MODEL_DIR = "./_model_cache"

# 第一次粗切单词数，18以下会切太碎影响翻译，22 以上太长会导致后续为字幕切分难以对齐
MAX_SPLIT_LENGTH = 20

## ======================== 配音设置 ======================== ##
# tts 选择 [openai, gpt_sovits, edge_tts, azure_tts]
TTS_METHOD = 'azure_tts'

# openai 选择的声音
OAI_VOICE = 'alloy'
# edge_tts 选择的声音
EDGE_VOICE = 'zh-CN-XiaoxiaoNeural'
# Azure key
AZURE_KEY = 'YOUR_AZURE_KEY'
AZURE_REGION = 'eastasia'
AZURE_VOICE = 'zh-CN-XiaoxiaoNeural'

# SoVITS角色配置
DUBBING_CHARACTER = 'Huanyuv2'

MIN_SPEED_FACTOR = 0.95
MAX_SPEED_FACTOR = 1.8

# 音频配置
MIN_SUBTITLE_DURATION = 4

# 配音视频中原始人声音量 0.1=10%
ORIGINAL_VOLUME = 0.1

# SoVits的参考音频模式
REFER_MODE = 3

## ======================== 语言模型 ======================== ##
# Spacy 模型
SPACY_MODEL_MAP = {
    "en": "en_core_web_md",
    "ru": "ru_core_news_md",
    "fr": "fr_core_news_md",
    "ja": "ja_core_news_md",
    "es": "es_core_news_md",
    "de": "de_core_news_md",
    "it": "it_core_news_md",
    
    # Not supported
    # "zh": "zh_core_web_md",
}

# 使用空格分割的语言
LANGUAGE_SPLIT_WITH_SPACE = ['en', 'es', 'fr', 'de', 'it', 'pt', 'nl', 'el', 'ru', 'ar', 'hi', 'pl', 'uk', 'vi', 'tr', 'ro', 'da', 'fi', 'hu', 'nb', 'sv']
# 不使用空格分割的语言
LANGUAGE_SPLIT_WITHOUT_SPACE = ['zh', 'ja', 'th', 'ko']

def get_joiner(language):
    if language in LANGUAGE_SPLIT_WITH_SPACE:
        return " "
    elif language in LANGUAGE_SPLIT_WITHOUT_SPACE:
        return ""
    else:
        raise ValueError(f"Unsupported language code: {language}")