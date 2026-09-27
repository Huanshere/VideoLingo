import spacy
from spacy.cli import download
from core.utils import rprint, load_key, except_handler, get_source_language

# Official spaCy 3.8 pipelines for further languages that auto detection can return;
# entries in config.yaml's spacy_model_map take precedence. Cantonese is written in Chinese.
DEFAULT_SPACY_MODELS = {
    "ko": "ko_core_news_md", "pt": "pt_core_news_md", "nl": "nl_core_news_md",
    "sv": "sv_core_news_md", "da": "da_core_news_md", "fi": "fi_core_news_md",
    "pl": "pl_core_news_md", "el": "el_core_news_md", "ro": "ro_core_news_md",
    "mk": "mk_core_news_md", "yue": "zh_core_web_md",
}
CONFIGURED_SPACY_MODELS = load_key("spacy_model_map")
SPACY_MODEL_MAP = {**DEFAULT_SPACY_MODELS, **CONFIGURED_SPACY_MODELS}

def get_spacy_model(language: str):
    """spaCy pipeline for the language, or None when spaCy has none (e.g. ar, th, vi)."""
    return SPACY_MODEL_MAP.get(language.lower())

def punctuation_nlp():
    """Multi-language tokenizer that splits sentences on punctuation only (no model download).

    Tokens carry no POS/dependency tags, so the later comma/connector/root splits simply do
    not fire and long sentences are left to the LLM split step.
    """
    nlp = spacy.blank("xx")
    nlp.add_pipe("sentencizer")
    return nlp

@except_handler("Failed to load NLP Spacy model")
def init_nlp():
    language = get_source_language()
    model = get_spacy_model(language)
    if model is None:
        rprint(f"[yellow]No spaCy pipeline for '{language}'; splitting sentences by punctuation only.[/yellow]")
        return punctuation_nlp()
    rprint(f"[blue]⏳ Loading NLP Spacy model: <{model}> ...[/blue]")
    try:
        nlp = spacy.load(model)
    except:
        rprint(f"[yellow]Downloading {model} model...[/yellow]")
        rprint("[yellow]If download failed, please check your network and try again.[/yellow]")
        if language.lower() in CONFIGURED_SPACY_MODELS:
            download(model)
            nlp = spacy.load(model)
        else:
            # A built-in default must not stop the pipeline (spaCy's download exits on failure).
            try:
                download(model)
                nlp = spacy.load(model)
            except (Exception, SystemExit) as exc:
                rprint(f"[yellow]Could not load {model} ({exc}); splitting sentences by punctuation only.[/yellow]")
                return punctuation_nlp()
    rprint("[green]✅ NLP Spacy model loaded successfully![/green]")
    return nlp

# --------------------
# define the intermediate files
# --------------------
SPLIT_BY_COMMA_FILE = "output/log/split_by_comma.txt"
SPLIT_BY_CONNECTOR_FILE = "output/log/split_by_connector.txt"
SPLIT_BY_MARK_FILE = "output/log/split_by_mark.txt"
