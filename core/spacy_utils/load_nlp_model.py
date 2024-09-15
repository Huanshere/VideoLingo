import os,sys
import spacy
from spacy.cli import download
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.step2_whisper import get_whisper_language
from config import SPACY_MODEL_MAP

def get_spacy_model(language: str):
    model = SPACY_MODEL_MAP.get(language.lower(), "en_core_web_sm")
    if language not in SPACY_MODEL_MAP:
        print(f"Spacy model does not support '{language}', using en_core_web_sm model as fallback...")
    return model

def init_nlp():
    try:
        from config import WHISPER_LANGUAGE
        language = "en" if WHISPER_LANGUAGE == "en" else get_whisper_language()
        model = get_spacy_model(language)
        print(f"⏳ Loading NLP Spacy model: <{model}> ...")
        try:
            nlp = spacy.load(model)
        except:
            print(f"Downloading {model} model...")
            download(model)
            nlp = spacy.load(model)
    except:
        raise ValueError(f"❌ Failed to load NLP Spacy model: {model}")
    print(f"✅ NLP Spacy model loaded successfully!")
    return nlp