import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import os,sys
import pandas as pd
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.spacy_utils.load_nlp_model import init_nlp
from core.step2_whisper import get_whisper_language
from config import get_joiner, WHISPER_LANGUAGE

def split_by_mark(nlp):
    language = get_whisper_language() if WHISPER_LANGUAGE == 'auto' else WHISPER_LANGUAGE # 考虑强制英文的情况
    joiner = get_joiner(language)
    print(f"🔍 正在使用 {language} 语言的拼接方式: '{joiner}'")
    chunks = pd.read_excel("output/log/cleaned_chunks.xlsx")
    chunks.text = chunks.text.apply(lambda x: x.strip('"'))
    
    # 用 joiner 拼接
    input_text = joiner.join(chunks.text.to_list())

    doc = nlp(input_text)
    assert doc.has_annotation("SENT_START")

    sentences_by_mark = [sent.text for sent in doc.sents]

    with open("output/log/sentence_by_mark.txt", "w", encoding="utf-8") as output_file:
        for sentence in sentences_by_mark:
            output_file.write(sentence + "\n")

    print("💾 Sentences split by punctuation marks saved to →  `sentences_by_mark.txt`")

if __name__ == "__main__":
    # nlp = init_nlp()
    # split_by_mark(nlp)

    s = """そうで。"""
    nlp = init_nlp()
    doc = nlp(s)
    print(doc)
    assert doc.has_annotation("SENT_START")

    sentences_by_mark = [sent.text for sent in doc.sents]
    print(sentences_by_mark)

