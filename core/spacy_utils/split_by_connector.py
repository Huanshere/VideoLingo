import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import os,sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from load_nlp_model import init_nlp

def analyze_connectors(doc, token):
    """
    Analyze whether a token is a connector that should trigger a sentence split.
    
    Processing logic and order:
    1. Check if the token is one of the target connectors (that, which, where, when).
    2. For 'that', check if it's part of a contraction (e.g., that's, that'll).
    3. For all connectors, check if they function as a 'mark' dependent of a verb.
    4. For 'which', 'where', 'when', check if they function as determiners or pronouns 
       for nouns or proper nouns.
    5. Default to splitting for 'which', 'where', 'when' if no other conditions are met.
    6. For 'and', 'or', 'but', check if they connect two independent clauses.
    """
    # Check if the token is one of the target connectors
    if token.text.lower() not in ["that", "which", "where", "when", "because", "but", "and", "or"]:
        return False, False
    
    if token.text.lower() == "that":
        if token.dep_ == "mark" and token.head.pos_ == "VERB":
            # Split if 'that' is a 'mark' dependent of a verb
            return True, False
        else:
            # Don't split for other uses of 'that'
            return False, False
    elif token.text.lower() != "that" and token.dep_ in ["det", "pron"] and token.head.pos_ in ["NOUN", "PROPN"]:
        # Don't split if 'which', 'where', 'when' are determiners or pronouns for nouns
        return False, False
    else:
        return True, False

def split_by_connectors(text, context_words=5, nlp=None):
    doc = nlp(text)
    sentences = [doc.text]  # init
    
    while True:
        # Handle each task with a single cut
        # avoiding the fragmentation of a sentence into multiple parts at the same time.
        split_occurred = False
        new_sentences = []
        
        for sent in sentences:
            doc = nlp(sent)
            start = 0
            
            for i, token in enumerate(doc):
                split_before, _ = analyze_connectors(doc, token)
                
                if i + 1 < len(doc) and doc[i + 1].text in ["'s", "'re", "'ve", "'ll", "'d"]:
                    continue
                
                left_words = doc[max(0, token.i - context_words):token.i]
                right_words = doc[token.i+1:min(len(doc), token.i + context_words + 1)]
                
                left_words = [word.text for word in left_words if not word.is_punct]
                right_words = [word.text for word in right_words if not word.is_punct]
                
                if len(left_words) >= context_words and len(right_words) >= context_words and split_before:
                    print(f"✂️  Split before '{token.text}': {' '.join(left_words)}| {token.text} {' '.join(right_words)}")
                    new_sentences.append(doc[start:token.i].text.strip())
                    start = token.i
                    split_occurred = True
                    break
            
            if start < len(doc):
                new_sentences.append(doc[start:].text.strip())
        
        if not split_occurred:
            break
        
        sentences = new_sentences
    
    return sentences

def split_sentences_main():
    nlp = init_nlp()
    # Read input sentences
    with open("output/log/sentence_by_comma.txt", "r", encoding="utf-8") as input_file:
        sentences = input_file.readlines()
    
    all_split_sentences = []
    # Process each input sentence
    for sentence in sentences:
        split_sentences = split_by_connectors(sentence.strip(), nlp = nlp)
        all_split_sentences.extend(split_sentences)
    
    # output to sentence_splitbymark.txt
    with open("output/log/sentence_splitbymark.txt", "w+", encoding="utf-8") as output_file:
        for sentence in all_split_sentences:
            output_file.write(sentence + "\n")

    print("💾 Sentences split by connectors saved to →  `sentence_splitbymark.txt`")

if __name__ == "__main__":
    # split_sentences_main()
    a = "and show the specific differences that make a difference between a breakaway that results in a goal in the NHL versus one that doesn't."
    print(split_by_connectors(a))