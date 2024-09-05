import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from load_nlp_model import init_nlp
import pandas as pd
from step2_whisper_stamped import get_whisper_language

def split_by_mark():
    language = get_whisper_language()
    # 支持的语言代码列表
    supported_languages = ['en', 'zh', 'es', 'fr', 'de', 'it', 'ja', 'pt', 'nl', 'el', 'ru', 'ar', 'hi', 'ko', 'pl', 'uk', 'vi', 'tr', 'th', 'ro', 'da', 'fi', 'hu', 'nb', 'sv']
    
    # 检查输入的语言是否支持
    if language not in supported_languages:
        raise ValueError(f"不支持的语言代码: {language}。支持的语言代码为: {', '.join(supported_languages)}")

    nlp = init_nlp()
    chunks = pd.read_excel("output/log/cleaned_chunks.xlsx")
    chunks.text = chunks.text.apply(lambda x: x.strip('"'))
    
    # 定义需要空格拼接的语言列表
    space_join_languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'nl', 'el', 'ru', 'pl', 'uk', 'ro', 'da', 'fi', 'hu', 'nb', 'sv']
    input_text = " ".join(chunks.text.to_list()) if language in space_join_languages else "".join(chunks.text.to_list())

    doc = nlp(input_text)
    assert doc.has_annotation("SENT_START")

    sentences_by_mark = [sent.text for sent in doc.sents]

    with open("output/log/sentence_by_mark.txt", "w", encoding="utf-8") as output_file:
        for sentence in sentences_by_mark:
            output_file.write(sentence + "\n")

    print("💾 Sentences split by punctuation marks saved to →  `sentences_by_mark.txt`")

if __name__ == "__main__":
    split_by_mark()