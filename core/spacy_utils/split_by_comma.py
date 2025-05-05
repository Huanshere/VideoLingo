import itertools
import os
import warnings
from core.utils import *
from core.spacy_utils.load_nlp_model import init_nlp, SPLIT_BY_COMMA_FILE, SPLIT_BY_MARK_FILE

warnings.filterwarnings("ignore", category=FutureWarning)

def is_valid_phrase(phrase):
    # 🔍 Check for subject and verb
    has_subject = any(token.dep_ in ["nsubj", "nsubjpass"] or token.pos_ == "PRON" for token in phrase)
    has_verb = any((token.pos_ == "VERB" or token.pos_ == 'AUX') for token in phrase)
    return (has_subject and has_verb)

def analyze_comma(start, doc, token):
    left_phrase = doc[max(start, token.i - 9):token.i]
    right_phrase = doc[token.i + 1:min(len(doc), token.i + 10)]
    
    suitable_for_splitting = is_valid_phrase(right_phrase) # and is_valid_phrase(left_phrase) # ! no need to chekc left phrase
    
    # 🚫 Remove punctuation and check word count
    left_words = [t for t in left_phrase if not t.is_punct]
    right_words = list(itertools.takewhile(lambda t: not t.is_punct, right_phrase)) # ! only check the first part of the right phrase
    
    if len(left_words) <= 3 or len(right_words) <= 3:
        suitable_for_splitting = False

    return suitable_for_splitting

def split_by_comma(text, nlp):
    doc = nlp(text)
    sentences = []
    start = 0
    
    for i, token in enumerate(doc):
        if token.text == "," or token.text == "，":
            suitable_for_splitting = analyze_comma(start, doc, token)
            
            if suitable_for_splitting:
                sentences.append(doc[start:token.i].text.strip())
                rprint(f"[yellow]✂️  Split at comma: {doc[start:token.i][-4:]},| {doc[token.i + 1:][:4]}[/yellow]")
                start = token.i + 1
    
    sentences.append(doc[start:].text.strip())
    return sentences

def split_by_comma_main(nlp):

    with open(SPLIT_BY_MARK_FILE, "r", encoding="utf-8") as input_file:
        sentences = input_file.readlines()

    all_split_sentences = []
    for sentence in sentences:
        split_sentences = split_by_comma(sentence.strip(), nlp)
        all_split_sentences.extend(split_sentences)

    with open(SPLIT_BY_COMMA_FILE, "w", encoding="utf-8") as output_file:
        for sentence in all_split_sentences:
            output_file.write(sentence + "\n")
    
    # delete the original file
    os.remove(SPLIT_BY_MARK_FILE)
    
    rprint(f"[green]💾 Sentences split by commas saved to →  `{SPLIT_BY_COMMA_FILE}`[/green]")

if __name__ == "__main__":
    nlp = init_nlp()
    split_by_comma_main(nlp)
    # nlp = init_nlp()
    # test = "So in the same frame, right there, almost in the exact same spot on the ice, Brown has committed himself, whereas McDavid has not."
    # print(split_by_comma(test, nlp))