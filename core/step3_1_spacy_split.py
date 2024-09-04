import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from spacy_utils.split_by_comma import split_by_comma_main
from spacy_utils.split_by_connector import split_sentences_main
from spacy_utils.split_by_mark import split_by_mark

# TODO 🚧 use smater way to split
def split_by_spacy():
    split_by_mark()
    split_by_comma_main()
    split_sentences_main()
    return

if __name__ == '__main__':
    split_by_spacy()