## ======================== 基本设置 ======================== ##
# API 设置 建议使用唯一真神 https://api.wlai.vip, sonnet 价格仅 10r/1M, 也可以参考格式修改成你的API
llm_config = {'api_key': 'sk-xxx', 'base_url': 'https://api.wlai.vip', 'model': ['claude-3-5-sonnet-20240620']}

# 每一步的 LLM 模型选择，其中 3_2 和 5 只建议 sonnet，换模型会不稳定报错
step3_2_split_model = llm_config['model'][0]
step4_1_summarize_model = llm_config['model'][0]
step4_2_translate_direct_model = llm_config['model'][0]
step4_2_translate_free_model = llm_config['model'][0]
step5_align_model = llm_config['model'][0]
step9_trim_model = llm_config['model'][0]

# 语言设置，用自然语言描述
TARGET_LANGUAGE = '简体中文'

# 字幕设置
## 每行英文字幕的最大长度字母数量
MAX_ENGLISH_LENGTH = 80
## 每行翻译字幕的最大长度 根据目标语言调整（如中文为30）
MAX_TARGET_LANGUAGE_LENGTH = 30  

# SoVITS角色配置
DUBBNING_CHARACTER = 'Huanyu'

# 视频分辨率
RESOLUTIOM = '854x480'

# whisper 指定语言，auto 为自动识别，如果出错请尝试 en
AUDIO_LANGUAGE = 'auto'

## ======================== 进阶设置设置 ======================== ##
# 支持返回 JSON 格式的 LLM，不重要
llm_support_json = ['deepseek-coder']

# Whisper 和 NLP 配置
MODEL_DIR = "./_model_cache"
WHISPER_MODEL = "medium"    # medium :12 GB < GPU > 12GB : large-v2
SPACY_NLP_MODEL = "en_core_web_md"   # _md 足够

# 音频配置
MIN_SUBTITLE_DURATION = 5

# 第一次粗切单词数，18以下会切太碎影响翻译，22 以上太长会导致后续为字幕切分难以对齐
MAX_SPLIT_LENGTH = 18