import os, sys
# 建议在 streamlit 页面中调整设置
## ======================== 基本设置 ======================== ##
# API 设置 建议使用唯一真神 https://api.wlai.vip/register?aff=TXMB, sonnet 价格仅 10r/1M。
# 申请令牌时勾选模型`claude-3-5-sonnet-20240620`，渠道建议选`默认渠道1.0`
API_KEY = 'sk-xxx'
BASE_URL = 'https://api2.wlai.vip'
MODEL = ['claude-3-5-sonnet-20240620']

# Replicate API 设置
REPLICATE_API_TOKEN = "xxx"

# 语言设置，用自然语言描述
TARGET_LANGUAGE = '简体中文'

# 字幕设置
# 每行字幕的最大长度字母数量
MAX_SUB_LENGTH = 80
# 输出字幕字号更大一些
TARGET_SUB_MULTIPLIER = 1.5

# 视频分辨率
RESOLUTIOM = '854x480'

## ======================== 进阶设置设置 ======================== ##
# Whisper 设置 [whisperx, whisperxapi, whisper_timestamped]
WHISPER_METHOD = 'whisperx'

# Whisper 指定识别语言
WHISPER_LANGUAGE = 'auto'

# 支持视频格式
ALLOWED_VIDEO_FORMATS = ['mp4', 'mov', 'avi', 'mkv', 'flv', 'wmv', 'webm']

# gpt多线程数量
MAX_WORKERS = 6

# 每一步的 LLM 模型选择，其中 3_2 和 5 只建议 sonnet，换模型会不稳定报错
step3_2_split_model = MODEL[0]
step4_1_summarize_model = MODEL[0]
step4_2_translate_direct_model = MODEL[0]
step4_2_translate_free_model = MODEL[0]
step5_align_model = MODEL[0]
step9_trim_model = MODEL[0]

# 支持返回 JSON 格式的 LLM，不重要
llm_support_json = []

## 设置趋动云 model dir
cloud = 1 if sys.platform.startswith('linux') else 0
if cloud: # 趋动云
    gemini_pretrain = os.getenv('GEMINI_PRETRAIN')
    cloud_model_dir = os.path.join(gemini_pretrain, "_model_cache") 

# GPT_SoVITS 和 uvr5 模型目录
MODEL_DIR = "./_model_cache" if not cloud else cloud_model_dir

# 音频配置
MIN_SUBTITLE_DURATION = 8

# 配音视频中原始人声音量 0.1=10%
ORIGINAL_VOLUME = 0.1

# 第一次粗切单词数，18以下会切太碎影响翻译，22 以上太长会导致后续为字幕切分难以对齐
MAX_SPLIT_LENGTH = 20

## ======================== 语言模型 ======================== ##
# Spacy model
SPACY_MODEL_MAP = {
    "en": "en_core_web_lg",
    "zh": "zh_core_web_lg",
    "es": "es_core_news_lg",
    "fr": "fr_core_news_lg",
    "de": "de_core_news_lg",
    "it": "it_core_news_lg",
    "ja": "ja_core_news_lg",
    "pt": "pt_core_news_lg",
    "nl": "nl_core_news_lg",
    "el": "el_core_news_lg",
    "ru": "ru_core_news_lg",
    "ar": "ar_core_news_lg",
    "hi": "hi_core_news_lg",
    "ko": "ko_core_news_lg",
    "pl": "pl_core_news_lg",
    "uk": "uk_core_news_lg",
    "vi": "vi_core_news_lg",
    "tr": "tr_core_news_lg",
    "th": "th_core_news_lg",
    "ro": "ro_core_news_lg",
    "da": "da_core_news_lg",
    "fi": "fi_core_news_lg",
    "hu": "hu_core_news_lg",
    "nb": "nb_core_news_lg",
    "sv": "sv_core_news_lg"
}

LANGUAGE_SPLIT_WITH_SPACE = ['en', 'es', 'fr', 'de', 'it', 'pt', 'nl', 'el', 'ru', 'ar', 'hi', 'pl', 'uk', 'vi', 'tr', 'ro', 'da', 'fi', 'hu', 'nb', 'sv']
LANGUAGE_SPLIT_WITHOUT_SPACE = ['zh', 'ja', 'th', 'ko']

def get_joiner(language):
    if language in LANGUAGE_SPLIT_WITH_SPACE:
        return " "
    elif language in LANGUAGE_SPLIT_WITHOUT_SPACE:
        return ""
    else:
        raise ValueError(f"不支持的语言代码: {language}")
    

# 配音设置 暂时弃用
# *SoVITS角色配置
DUBBING_CHARACTER = 'Huanyu'