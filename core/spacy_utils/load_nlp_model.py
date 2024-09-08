import os,sys
import spacy
from spacy.cli import download
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.step2_whisper import get_whisper_language
from config import SPACY_MODEL_MAP

def get_spacy_model(language: str):
    model = SPACY_MODEL_MAP.get(language.lower(), "en_core_web_sm")
    if language not in SPACY_MODEL_MAP:
        print(f"Spacy 模型不支持'{language}'，使用 en_core_web_sm 模型作为后备选项...")
    return model

def init_nlp():
    try:
        from config import WHISPER_LANGUAGE
        language = "en" if WHISPER_LANGUAGE == "en" else get_whisper_language()
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