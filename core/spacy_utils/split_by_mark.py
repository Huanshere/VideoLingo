import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import pandas as pd
import os,sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from load_nlp_model import init_nlp

def split_by_mark():
    nlp = init_nlp()
    df = pd.read_excel("output/log/cleaned_chunks.xlsx")
    df['text'] = df['text'].str.strip('"').str.strip()
    input_text = " ".join(df['text'])
    doc = nlp(input_text)
    assert doc.has_annotation("SENT_START")

    sentences_by_mark = [sent.text for sent in doc.sents]

    with open("output/log/sentence_by_mark.txt", "w", encoding="utf-8") as output_file:
        for sentence in sentences_by_mark:
            output_file.write(sentence + "\n")

    print("💾 Sentences split by punctuation marks saved to →  `sentences_by_mark.txt`")

if __name__ == "__main__":
    split_by_mark()