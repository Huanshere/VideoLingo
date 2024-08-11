## ======================== 基本设置 ======================== ##
# API 设置
# 建议使用聚合站例如 https://www.ohmygpt.com/settings, 如需其他openai-like API请按照高级选项中的`llm_config`配置
OHMYGPT_API_KEY = ''  

# 语言设置
TARGET_LANGUAGE = '简体中文'  # 用自然语言描述

# 字幕设置
MAX_ENGLISH_LENGTH = 80          # 每行英文字幕的最大长度
MAX_TARGET_LANGUAGE_LENGTH = 30  # 根据目标语言调整（如中文为30）

# SoVITS角色配置
DUBBNING_CHARACTER = 'Huanyu' 

## ======================== 高级选项======================== ##
# 每一步的 LLM 模型选择，此配置适用于ohmygpt，sonnet 较贵，成本敏感可以全部更换为 Qwen
# 任务难度：简单🍰 中等🤔 困难🔥
step3_2_split_model =  "claude-3-5-sonnet-20240620"              # 🔥 建议Sonnet
step4_1_summarize_model = "TA/Qwen/Qwen1.5-72B-Chat"             # 🤔
step4_2_translate_direct_model ="TA/Qwen/Qwen1.5-72B-Chat"       # 🍰
step4_2_translate_free_model =  "TA/Qwen/Qwen1.5-72B-Chat"       # 🤔
step5_align_model = "claude-3-5-sonnet-20240620"                 # 🔥 建议Sonnet
step9_trim_model = "TA/Qwen/Qwen1.5-72B-Chat"                    # 🍰

# LLM 配置，你可以添加更多 API 如 openai, BASE_URL, MODEL
OPEN_ROUTER_API_KEY = ''  
llm_config: list = [
    {
        'name': 'ohmygpt',
        'api_key': OHMYGPT_API_KEY,
        'base_url': 'https://api.ohmygpt.com',
        'model': ['deepseek-coder','gpt-4o', 'claude-3-5-sonnet-20240620', "TA/Qwen/Qwen1.5-72B-Chat"],
    },
    {
        'name': 'openrouter',
        'api_key': OPEN_ROUTER_API_KEY,
        'base_url': 'https://openrouter.ai/api/v1',
        'model': ['deepseek/deepseek-coder', 'anthropic/claude-3.5-sonnet'],
    },
]

# 支持返回 JSON 格式的 LLM
llm_support_json = ['deepseek-coder', 'gpt-4o']

# Whisper 和 NLP 配置
WHISPER_MODEL = "medium"    # medium :12 GB < GPU > 12GB : large-v2
SPACY_NLP_MODEL = "en_core_web_md"   # _md 足够

# 音频配置
MIN_SUBTITLE_DURATION = 5

