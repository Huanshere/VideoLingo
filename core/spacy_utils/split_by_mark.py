import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import os,sys
import pandas as pd
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.spacy_utils.load_nlp_model import init_nlp
from core.config_utils import load_key, get_joiner
from rich import print

def split_by_mark(nlp):
    whisper_language = load_key("whisper.language")
    language = load_key("whisper.detected_language") if whisper_language == 'auto' else whisper_language # consider force english case
    joiner = get_joiner(language)
    print(f"[blue]🔍 Using {language} language joiner: '{joiner}'[/blue]")
    chunks = pd.read_excel("output/log/cleaned_chunks.xlsx")
    chunks.text = chunks.text.apply(lambda x: x.strip('"').strip(""))
    
    # join with joiner
    input_text = joiner.join(chunks.text.to_list())

    doc = nlp(input_text)
    assert doc.has_annotation("SENT_START")

    sentences_by_mark = [sent.text for sent in doc.sents]

    with open("output/log/sentence_by_mark.txt", "w", encoding="utf-8") as output_file:
        for i, sentence in enumerate(sentences_by_mark):
            if i > 0 and sentence.strip() in [',', '.', '，', '。', '？', '！']:
                # ! If the current line contains only punctuation, merge it with the previous line, this happens in Chinese, Japanese, etc.
                output_file.seek(output_file.tell() - 1, os.SEEK_SET)  # Move to the end of the previous line
                output_file.write(sentence)  # Add the punctuation
            else:
                output_file.write(sentence + "\n")
    
    print("[green]💾 Sentences split by punctuation marks saved to →  `sentences_by_mark.txt`[/green]")

if __name__ == "__main__":
    nlp = init_nlp()
    split_by_mark(nlp)
