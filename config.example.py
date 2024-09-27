# 标* 为不会出现在streamlit页面中的进阶设置，仅能在config.py中手动修改
## ======================== 基本设置 ======================== ##
# API settings
API_KEY = 'YOUR_API_KEY'
BASE_URL = 'https://yunwu.zeabur.app'
MODEL = 'claude-3-5-sonnet-20240620'

# Replicate API 设置
REPLICATE_API_TOKEN = 'YOUR_API_TOKEN'

# 语言设置，写入prompt中，用自然语言描述即可
TARGET_LANGUAGE = '简体中文'

## 字幕设置
# *每行字幕的最大长度 字母数量
MAX_SUB_LENGTH = 70
# *翻译字幕比源字幕字号更大一些，会影响切割字幕的参考长度
TARGET_SUB_MULTIPLIER = 1.2

# 视频分辨率 [0x0, 640x360, 1920x1080]  0x0会生成一个0秒的黑色视频占位
RESOLUTION = '640x360'

# 网页显示语言，auto为根据系统自动检测 [zh_CN, en_US, auto]
DISPLAY_LANGUAGE = 'zh_CN'

## ======================== 进阶设置设置 ======================== ##
# *下载youtube默认分辨率 [360, 1080, best]
YTB_RESOLUTION = '1080'

# Whisper 设置 [whisperx, whisperxapi]
WHISPER_METHOD = 'whisperxapi'

# *Whisper 指定识别语言 [auto, en, ...] auto为自动检测，en为强制转译为英文
WHISPER_LANGUAGE = 'auto'

# *llm 多线程访问数量
MAX_WORKERS = 6

# *第一次粗切最大单词数量，18以下会切太碎影响翻译，22 以上太长会导致后续为字幕切分难以对齐
MAX_SPLIT_LENGTH = 20

# *是否在提取专业名词后，翻译之前暂停，给用户手动调整术语表 output\log\terminology.json
PAUSE_BEFORE_TRANSLATE = False

## ======================== 配音设置 ======================== ##
# tts 选择 [openai, gpt_sovits, azure_tts, fish_tts]
TTS_METHOD = 'fish_tts'

# openai tts-1 接口配置
OAI_VOICE = 'alloy'
OAI_TTS_API_KEY = 'YOUR_API_KEY'
OAI_TTS_API_BASE_URL = 'https://yunwu.zeabur.app'

# Azure 配置
# API文档及申请：https://learn.microsoft.com/zh-cn/azure/ai-services/speech-service/get-started-text-to-speech?tabs=windows%2Cterminal&pivots=programming-language-python
# voice列表见：https://learn.microsoft.com/zh-cn/azure/ai-services/speech-service/language-support?tabs=tts#prebuilt-neural-voices
# 在线体验voice：https://speech.microsoft.com/portal/voicegallery
AZURE_KEY = 'YOUR_API_KEY'
AZURE_REGION = 'eastasia'
AZURE_VOICE = 'zh-CN-XiaoxiaoMultilingualNeural' # 推荐女声 'zh-CN-XiaoxiaoMultilingualNeural' 男声 "zh-CN-YunyiMultilingualNeural"

# SoVITS角色配置
DUBBING_CHARACTER = 'Huanyuv2'
# SoVits的参考音频模式
REFER_MODE = 3

# FishTTS API
FISH_TTS_API_KEY = 'YOUR_API_KEY'
# FishTTS 角色 确保在下方存在
FISH_TTS_CHARACTER = '丁真'
# *FishTTS角色列表 "角色名" : "角色ID"
FISH_TTS_CHARACTER_ID_DICT = {
    'AD学姐': '7f92f8afb8ec43bf81429cc1c9199cb1',
    '丁真': '54a5170264694bfc8e9ad98df7bd89c3',
    '赛马娘': '0eb38bc974e1459facca38b359e13511',
    '蔡徐坤': 'e4642e5edccd4d9ab61a69e82d4f8a14',
    '芙宁娜': '1aacaeb1b840436391b835fd5513f4c4',
    '雷军': '738d0cc1a3e9430a9de2b544a466a7fc',
    '邓紫棋': '3b55b3d84d2f453a98d8ca9bb24182d6',
    '郭德纲': '7c66db6e457c4d53b1fe428a8c547953',
}
# *FishTTS 音量增益，官方模型一般音量偏小，建议增益1.5
FISH_TTS_VOLUME = 1.5

# *音频的速度范围控制，实测1~1.35 之间效果自然
MIN_SPEED_FACTOR = 1
MAX_SPEED_FACTOR = 1.35
NORMAL_SPEED_FACTOR = 1.2 # 认为的正常语速

# *生成配音任务时合并音频配置，建议略大于下面的数
MIN_SUBTITLE_DURATION = 3
# * 翻译后裁切仅仅对时长大于X的进行
MIN_TRIM_DURATION = 2

# 压制配音视频中原始人声音量 0.1=10% or 0
ORIGINAL_VOLUME = 0.1

## ======================== 额外设定 请勿修改 ======================== ##
# Whisper 模型目录
MODEL_DIR = "./_model_cache"

# 支持的上传视频格式
ALLOWED_VIDEO_FORMATS = ['mp4', 'mov', 'avi', 'mkv', 'flv', 'wmv', 'webm']

# 支持返回 JSON 格式的 LLM，不重要
llm_support_json = ['deepseek-coder']

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