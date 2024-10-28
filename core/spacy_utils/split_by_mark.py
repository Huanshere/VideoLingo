import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import os, sys
import pandas as pd
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.spacy_utils.load_nlp_model import init_nlp
from core.step2_whisper import get_whisper_language
from core.config_utils import load_key, get_joiner
from rich import print

def split_by_mark(nlp):
    whisper_language = load_key("whisper.language")
    language = get_whisper_language() if whisper_language == 'auto' else whisper_language
    joiner = get_joiner(language)
    print(f"[blue]🔍 Using {language} language joiner: '{joiner}'[/blue]")
    
    chunks = pd.read_excel("output/log/cleaned_chunks.xlsx")
    chunks.text = chunks.text.apply(lambda x: x.strip('"'))
    
    input_text = joiner.join(chunks.text.to_list())

    # Use spaCy for initial sentence splitting
    doc = nlp(input_text)
    sentences = [sent.text.strip() for sent in doc.sents]

    # Further process sentences
    processed_sentences = []
    current_sentence = ""
    for sentence in sentences:
        if re.match(r'^[,，]$', sentence):
            # If the sentence is just a comma, append it to the previous sentence
            if current_sentence:
                current_sentence += sentence
            else:
                current_sentence = sentence
        elif re.search(r'[。！？…\.!?\…]$', sentence):
            # If the sentence ends with sentence-ending punctuation
            if current_sentence:
                processed_sentences.append(current_sentence + sentence)
                current_sentence = ""
            else:
                processed_sentences.append(sentence)
        else:
            # For other cases, accumulate the sentence
            current_sentence += sentence

    # Handle any remaining text
    if current_sentence:
        processed_sentences.append(current_sentence)

    with open("output/log/sentence_by_mark.txt", "w", encoding="utf-8") as output_file:
        for sentence in processed_sentences:
            if sentence.strip():  # Only write non-empty sentences
                output_file.write(sentence.strip() + "\n")
    
    print("[green]💾 Sentences split by punctuation marks saved to →  `sentences_by_mark.txt`[/green]")

if __name__ == "__main__":
    nlp = init_nlp()
    split_by_mark(nlp)
