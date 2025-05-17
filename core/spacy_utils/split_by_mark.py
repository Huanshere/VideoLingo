import os
import pandas as pd
import warnings
from core.spacy_utils.load_nlp_model import init_nlp, SPLIT_BY_MARK_FILE
from rich import print as rprint

warnings.filterwarnings("ignore", category=FutureWarning)

def split_by_mark(nlp):
    # get merged result
    merged_chunks = pd.read_excel("output/log/merged_by_speaker.xlsx")
    input_text = "\n".join(merged_chunks.text)
    
    # split by mark
    doc = nlp(input_text)
    assert doc.has_annotation("SENT_START")

    # skip - and ...
    sentences_by_mark = []
    current_sentence = []
    
    # iterate all sentences
    for sent in doc.sents:
        text = sent.text.strip()
        
        # check if the current sentence ends with - or ...
        if current_sentence and (
            text.startswith('-') or 
            text.startswith('...') or
            current_sentence[-1].endswith('-') or
            current_sentence[-1].endswith('...')
        ):
            current_sentence.append(text)
        else:
            if current_sentence:
                sentences_by_mark.append(' '.join(current_sentence))
                current_sentence = []
            current_sentence.append(text)
    
    # add the last sentence
    if current_sentence:
        sentences_by_mark.append(' '.join(current_sentence))

    with open(SPLIT_BY_MARK_FILE, "w", encoding="utf-8") as output_file:
        for i, sentence in enumerate(sentences_by_mark):
            if i > 0 and sentence.strip() in [',', '.', '，', '。', '？', '！']:
                # 只包含标点的行并到上一行
                output_file.seek(output_file.tell() - 1, os.SEEK_SET)
                output_file.write(sentence)
            else:
                output_file.write(sentence + "\n")
    
    rprint(f"[green]💾 Sentences split by punctuation marks saved to →  `{SPLIT_BY_MARK_FILE}`[/green]")

if __name__ == "__main__":
    nlp = init_nlp()
    split_by_mark(nlp)
