import spacy
from spacy.cli import download
from core.utils import rprint, load_key, except_handler

SPACY_MODEL_MAP = load_key("spacy_model_map")

def get_spacy_model(language: str):
    model = SPACY_MODEL_MAP.get(language.lower(), "en_core_web_md")
    if language not in SPACY_MODEL_MAP:
        rprint(f"[yellow]Spacy model does not support '{language}', using en_core_web_md model as fallback...[/yellow]")
    return model

@except_handler("Failed to load NLP Spacy model")
def init_nlp():
    language = "en" if load_key("whisper.language") == "en" else load_key("whisper.detected_language")
    model = get_spacy_model(language)
    rprint(f"[blue]⏳ Loading NLP Spacy model: <{model}> ...[/blue]")
    try:
        nlp = spacy.load(model)
    except:
        rprint(f"[yellow]Downloading {model} model...[/yellow]")
        rprint("[yellow]If download failed, please check your network and try again.[/yellow]")
        download(model)
        nlp = spacy.load(model)
    rprint("[green]✅ NLP Spacy model loaded successfully![/green]")
    return nlp

# --------------------
# define the intermediate files
# --------------------
SPLIT_BY_COMMA_FILE = "output/log/split_by_comma.txt"
SPLIT_BY_CONNECTOR_FILE = "output/log/split_by_connector.txt"
SPLIT_BY_MARK_FILE = "output/log/split_by_mark.txt"
