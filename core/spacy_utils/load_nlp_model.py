import os,sys
import spacy
from spacy.cli import download
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import SPACY_NLP_MODEL

def init_nlp():
    print(f"⏳ Loading NLP Spacy model: <{SPACY_NLP_MODEL}> ...")
    try:
        nlp = spacy.load(SPACY_NLP_MODEL)
    except:
        print(f"Downloading {SPACY_NLP_MODEL} model...")
        download(SPACY_NLP_MODEL)
        nlp = spacy.load(SPACY_NLP_MODEL)
    print(f"✅ NLP Spacy model loaded successfully!")
    return nlp