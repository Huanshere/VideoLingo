import os,sys
import spacy
from spacy.cli import download
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.step2_whisper_stamped import get_whisper_language

def get_spacy_model(language: str):
    language_map = {
        "en": "en_core_web_sm",
        "zh": "zh_core_web_sm",
        "es": "es_core_news_sm",
        "fr": "fr_core_news_sm",
        "de": "de_core_news_sm",
        "it": "it_core_news_sm",
        "ja": "ja_core_news_sm",
        "pt": "pt_core_news_sm",
        "nl": "nl_core_news_sm",
        "el": "el_core_news_sm",
        "ru": "ru_core_news_sm",
        "ar": "ar_core_news_sm",
        "hi": "hi_core_news_sm",
        "ko": "ko_core_news_sm",
        "pl": "pl_core_news_sm",
        "uk": "uk_core_news_sm",
        "vi": "vi_core_news_sm",
        "tr": "tr_core_news_sm",
        "th": "th_core_news_sm",
        "ro": "ro_core_news_sm",
        "da": "da_core_news_sm",
        "fi": "fi_core_news_sm",
        "hu": "hu_core_news_sm",
        "nb": "nb_core_news_sm",
        "sv": "sv_core_news_sm"
    }

    model = language_map.get(language.lower(), "en_core_web_sm")
    if language not in language_map:
        print(f"Spacy 模型不支持'{language}'，使用 en_core_web_sm 模型作为后备选项...")
    return model

def init_nlp():
    try:
        from config import WHISPER_LANGUAGE
        if WHISPER_LANGUAGE == "en":
            language = "en"
        else:
            language = get_whisper_language()
        model = get_spacy_model(language)
        print(f"⏳ 正在加载 NLP Spacy 模型: <{model}> ...")
        try:
            nlp = spacy.load(model)
        except:
            print(f"正在下载 {model} 模型...")
            download(model)
            nlp = spacy.load(model)
    except:
        print(f"未检测到语言，使用 en_core_web_sm 模型作为后备选项...")
        model = "en_core_web_sm"
        try:
            nlp = spacy.load(model)
        except:
            print(f"正在下载 {model} 模型...")
            download(model)
            nlp = spacy.load(model)
    print(f"✅ NLP Spacy 模型加载成功！")
    return nlp