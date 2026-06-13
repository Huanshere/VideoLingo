import os
import pandas as pd
import warnings
from core.spacy_utils.load_nlp_model import init_nlp, SPLIT_BY_MARK_FILE
from core.utils.config_utils import load_key, get_joiner
from core.utils.models import _2_ASR_SEGMENTS, _2_CLEANED_CHUNKS
from rich import print as rprint

warnings.filterwarnings("ignore", category=FutureWarning)

MAX_NLP_INPUT_BYTES = 40000

def _clean_text(value):
    if pd.isna(value):
        return ''
    return str(value or '').strip().strip('"').strip()

def _split_text_by_bytes(text, max_bytes=MAX_NLP_INPUT_BYTES):
    parts = []
    current = ''
    for char in text:
        candidate = current + char
        if current and len(candidate.encode('utf-8')) > max_bytes:
            parts.append(current)
            current = char
        else:
            current = candidate
    if current:
        parts.append(current)
    return parts

def _merge_units_by_bytes(units, joiner, max_bytes=MAX_NLP_INPUT_BYTES):
    batches = []
    current = ''
    for unit in units:
        if not unit:
            continue
        candidate = unit if not current else current + joiner + unit
        if current and len(candidate.encode('utf-8')) > max_bytes:
            batches.append(current)
            current = unit
        else:
            current = candidate
    if current:
        batches.append(current)
    return batches

def _load_nlp_inputs(joiner):
    if os.path.exists(_2_ASR_SEGMENTS):
        segments = pd.read_excel(_2_ASR_SEGMENTS)
        texts = [_clean_text(text) for text in segments.get('text', [])]
        texts = [text for text in texts if text]
        if texts:
            rprint(f"[blue]🔍 Using ASR segment text for NLP splitting: {len(texts)} segment(s)[/blue]")
            return [part for text in texts for part in _split_text_by_bytes(text)]

    rprint(f"[yellow]⚠️ {_2_ASR_SEGMENTS} not found or empty, rebuilding NLP text from {_2_CLEANED_CHUNKS}.[/yellow]")
    chunks = pd.read_excel(_2_CLEANED_CHUNKS)
    texts = [_clean_text(text) for text in chunks.text.to_list()]
    return _merge_units_by_bytes(texts, joiner)

def split_by_mark(nlp):
    whisper_language = load_key("whisper.language")
    language = load_key("whisper.detected_language") if whisper_language == 'auto' else whisper_language # consider force english case
    joiner = get_joiner(language)
    rprint(f"[blue]🔍 Using {language} language joiner: '{joiner}'[/blue]")
    input_texts = _load_nlp_inputs(joiner)

    # skip - and ...
    sentences_by_mark = []
    current_sentence = []
    
    # iterate all sentences
    for input_text in input_texts:
        doc = nlp(input_text)
        assert doc.has_annotation("SENT_START")
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
                    sentences_by_mark.append(joiner.join(current_sentence))
                    current_sentence = []
                current_sentence.append(text)
    
    # add the last sentence
    if current_sentence:
        sentences_by_mark.append(joiner.join(current_sentence))

    with open(SPLIT_BY_MARK_FILE, "w", encoding="utf-8") as output_file:
        for i, sentence in enumerate(sentences_by_mark):
            if i > 0 and sentence.strip() in [',', '.', '，', '。', '？', '！']:
                # ! If the current line contains only punctuation, merge it with the previous line, this happens in Chinese, Japanese, etc.
                output_file.seek(output_file.tell() - 1, os.SEEK_SET)  # Move to the end of the previous line
                output_file.write(sentence)  # Add the punctuation
            else:
                output_file.write(sentence + "\n")
    
    rprint(f"[green]💾 Sentences split by punctuation marks saved to →  `{SPLIT_BY_MARK_FILE}`[/green]")

if __name__ == "__main__":
    nlp = init_nlp()
    split_by_mark(nlp)
