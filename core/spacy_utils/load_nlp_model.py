import os,sys,json
import spacy
from spacy.cli import download
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.step2_whisperapi import get_whisper_language

def get_spacy_model(language: str):
    language_map = {
        "english": "en_core_web_sm",
        "chinese": "zh_core_web_sm",
        "spanish": "es_core_news_sm",
        "french": "fr_core_news_sm",
        "german": "de_core_news_sm",
        "italian": "it_core_news_sm",
        "japanese": "ja_core_news_sm",
        "portuguese": "pt_core_news_sm",
        "dutch": "nl_core_news_sm",
        "greek": "el_core_news_sm",
        "russian": "ru_core_news_sm",
        "arabic": "ar_core_news_sm",
        "hindi": "hi_core_news_sm",
        "korean": "ko_core_news_sm",
        "polish": "pl_core_news_sm",
        "ukrainian": "uk_core_news_sm",
        "vietnamese": "vi_core_news_sm",
        "turkish": "tr_core_news_sm",
        "thai": "th_core_news_sm",
        "romanian": "ro_core_news_sm",
        "danish": "da_core_news_sm",
        "finnish": "fi_core_news_sm",
        "hungarian": "hu_core_news_sm",
        "norwegian": "nb_core_news_sm",
        "swedish": "sv_core_news_sm"
    }

    model = language_map.get(language.lower(), "en_core_web_sm")
    if language not in language_map:
        print(f"Spacy 模型不支持'{language}'，使用 en_core_web_sm 模型作为后备选项...")
    return model

def init_nlp():
    try:
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