import os,sys
import spacy
from spacy.cli import download
from rich import print
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.config_utils import load_key

SPACY_MODEL_MAP = load_key("spacy_model_map")

def get_spacy_model(language: str):
    model = SPACY_MODEL_MAP.get(language.lower(), "en_core_web_md")
    if language not in SPACY_MODEL_MAP:
        print(f"[yellow]Spacy model does not support '{language}', using en_core_web_md model as fallback...[/yellow]")
    return model

def init_nlp():
    try:
        language = "en" if load_key("whisper.language") == "en" else load_key("whisper.detected_language")
        model = get_spacy_model(language)
        print(f"[blue]⏳ Loading NLP Spacy model: <{model}> ...[/blue]")
        try:
            nlp = spacy.load(model)
        except:
            print(f"[yellow]Downloading {model} model...[/yellow]")
            print("[yellow]If download failed, please check your network and try again.[/yellow]")
            download(model)
            nlp = spacy.load(model)
    except:
        raise ValueError(f"❌ Failed to load NLP Spacy model: {model}")
    print(f"[green]✅ NLP Spacy model loaded successfully![/green]")
    return nlp