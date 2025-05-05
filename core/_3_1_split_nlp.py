from core.spacy_utils import *
from core.utils.models import _3_1_SPLIT_BY_NLP
from core.utils import check_file_exists

@check_file_exists(_3_1_SPLIT_BY_NLP)
def split_by_spacy():
    nlp = init_nlp()
    split_by_mark(nlp)
    split_by_comma_main(nlp)
    split_sentences_main(nlp)
    split_long_by_root_main(nlp)
    return

if __name__ == '__main__':
    split_by_spacy()