# 建议在 streamlit 页面中调整设置
# Recommended to adjust settings in the streamlit page
## ======================== 基本设置 ======================== ##
## ======================== Basic Settings ======================== ##

# API Settings：
API_KEY = 'sk-xxx'
BASE_URL = 'https://api.siliconflow.cn'
MODEL = ['Qwen/Qwen2.5-72B-Instruct']

# Replicate API 设置
# Replicate API settings for using whisperX
REPLICATE_API_TOKEN = 'xxx'

# 语言设置，用自然语言描述
# Language settings, described in natural language
TARGET_LANGUAGE = '简体中文'

# 字幕设置
# Subtitle settings
# 每行字幕的最大长度字母数量
# Maximum number of characters per line of subtitle
MAX_SUB_LENGTH = 75
# 输出字幕字号更大一些
# Increase the font size of the output subtitles
TARGET_SUB_MULTIPLIER = 1.2

# 视频分辨率
# Video resolution
RESOLUTION = '640x360'

# 显示语言
# Display language
DISPLAY_LANGUAGE = 'zh_CN'

## ======================== 进阶设置设置 ======================== ##
## ======================== Advanced Settings ======================== ##

# Whisper 设置 [whisperx, whisperxapi, whisper_timestamped]
# Whisper settings [whisperx, whisperxapi, whisper_timestamped]
WHISPER_METHOD = 'whisperxapi'

# 预留给 whisper_timestamped 的模型，英语场景下 medium 甚至比 large-v2 的时间轴还准
# Reserved for whisper_timestamped model, in English scenarios, medium is even more accurate in timeline than large-v2
WHISPER_MODEL = 'medium'

# Whisper 指定识别语言
# Specify recognition language for Whisper
WHISPER_LANGUAGE = 'auto'

# 支持视频格式
# Supported video formats
ALLOWED_VIDEO_FORMATS = ['mp4', 'mov', 'avi', 'mkv', 'flv', 'wmv', 'webm']

# gpt多线程数量
# Number of GPT multi-threads
MAX_WORKERS = 6

# 每一步的 LLM 模型选择
# LLM model selection for each step
step3_2_split_model = MODEL[0]
step4_1_summarize_model = MODEL[0]
step4_2_translate_direct_model = MODEL[0]
step4_2_translate_free_model = MODEL[0]
step5_align_model = MODEL[0]
step9_trim_model = MODEL[0]

# 支持返回 JSON 格式的 LLM，不重要
# LLMs that support returning JSON format, not important
llm_support_json = ['deepseek-coder']

# Whisper 模型目录
# Whisper model directory
MODEL_DIR = "./_model_cache"

# 第一次粗切单词数，18以下会切太碎影响翻译，22 以上太长会导致后续为字幕切分难以对齐
# Number of words for initial rough cut, below 18 will cut too finely affecting translation, above 22 will be too long making it difficult to align for subtitle splitting
MAX_SPLIT_LENGTH = 20

# 配音设置
# Dubbing settings
# SoVITS角色配置
# SoVITS character configuration
DUBBING_CHARACTER = 'Huanyuv2'

MIN_SPEED_FACTOR = 0.9
MAX_SPEED_FACTOR = 1.8

# 音频配置
# Audio configuration
MIN_SUBTITLE_DURATION = 5

# 配音视频中原始人声音量 0.1=10%
# Original voice volume in dubbed video 0.1=10%
ORIGINAL_VOLUME = 0.1

## ======================== 语言模型 ======================== ##
## ======================== Language Models ======================== ##

# Spacy model
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
# Languages that split with space
LANGUAGE_SPLIT_WITH_SPACE = ['en', 'es', 'fr', 'de', 'it', 'pt', 'nl', 'el', 'ru', 'ar', 'hi', 'pl', 'uk', 'vi', 'tr', 'ro', 'da', 'fi', 'hu', 'nb', 'sv']
# 不使用空格分割的语言
# Languages that split without space
LANGUAGE_SPLIT_WITHOUT_SPACE = ['zh', 'ja', 'th', 'ko']

def get_joiner(language):
    if language in LANGUAGE_SPLIT_WITH_SPACE:
        return " "
    elif language in LANGUAGE_SPLIT_WITHOUT_SPACE:
        return ""
    else:
        raise ValueError(f"Unsupported language code: {language}")