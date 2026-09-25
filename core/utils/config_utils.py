from ruamel.yaml import YAML
import threading
import unicodedata

CONFIG_PATH = 'config.yaml'
lock = threading.Lock()

yaml = YAML()
yaml.preserve_quotes = True

# -----------------------
# load & update config
# -----------------------

def load_key(key):
    with lock:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as file:
            data = yaml.load(file)

    keys = key.split('.')
    value = data
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            raise KeyError(f"Key '{k}' not found in configuration")
    return value

def load_key_or(key, default):
    """Read an optional key; config.yaml files written before the key existed keep working."""
    try:
        return load_key(key)
    except KeyError:
        return default

def update_key(key, new_value, add_missing=False):
    """Set an existing key; add_missing=True also creates a new leaf (settings added after the user's config.yaml)."""
    with lock:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as file:
            data = yaml.load(file)

        keys = key.split('.')
        current = data
        for k in keys[:-1]:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return False

        if isinstance(current, dict) and (keys[-1] in current or add_missing):
            current[keys[-1]] = new_value
            # Keep manual source-language changes atomic for UI and CLI callers.
            if key == "whisper.language" and new_value != "auto":
                current["detected_language"] = new_value
            with open(CONFIG_PATH, 'w', encoding='utf-8') as file:
                yaml.dump(data, file)
            return True
        else:
            raise KeyError(f"Key '{keys[-1]}' not found in configuration")
        
# basic utils
def get_source_language():
    whisper = load_key("whisper")
    language = whisper["language"]
    if language == "auto":
        language = whisper.get("detected_language")
    if not isinstance(language, str) or not language or language == "auto":
        raise ValueError("Source language is unknown. Run transcription first or select a language.")
    return language


# Written without spaces between words. Any other language (everything else Qwen3-ASR or
# WhisperX can detect, e.g. ko, vi, pt, ar) joins with a space unless config.yaml says otherwise.
LANGUAGES_WITHOUT_SPACE = {"zh", "yue", "ja", "th", "lo", "km", "my", "bo"}


def get_joiner(language):
    if language in load_key_or('language_split_with_space', []):
        return " "
    elif language in load_key_or('language_split_without_space', []):
        return ""
    if not isinstance(language, str) or not language or language == "auto":
        raise ValueError(f"Unsupported language code: {language!r}")
    return "" if language.lower() in LANGUAGES_WITHOUT_SPACE else " "


# Scripts that are written without spaces; their letters never get a space from join_words.
_UNSPACED_SCRIPTS = ("CJK", "HIRAGANA", "KATAKANA", "HALFWIDTH KATAKANA", "IDEOGRAPHIC", "BOPOMOFO",
                     "THAI", "LAO", "KHMER", "MYANMAR", "TIBETAN")


def _spaced_word_char(char):
    """A letter or digit of a script written with spaces (Latin, Cyrillic, Hangul, digits, ...)."""
    if not char.isalnum():
        return False
    try:
        return not unicodedata.name(char).startswith(_UNSPACED_SCRIPTS)
    except ValueError:
        return True


def join_words(words, joiner):
    """Join words/tokens with the language joiner, keeping code-switched words apart.

    With the "" joiner (zh/ja/th...), a space is added only between two words of spaced
    scripts: when the left part ends and the right part starts with such a letter/digit
    ("Hello" + "Fiona" -> "Hello Fiona"), or the left ends with ASCII ,.!?;: and the right
    starts with such a letter ("Hello," + "Fiona"). CJK next to CJK and CJK next to Latin stay
    unspaced as before ("有个" + "meeting" + "啊" -> "有个meeting啊"). The " " joiner is unchanged.
    """
    words = [str(word) for word in words]
    if joiner:
        return joiner.join(words)
    text = ""
    for word in words:
        if text and word:
            left, right = text[-1], word[0]
            if _spaced_word_char(right) and (_spaced_word_char(left) or (left in ",.!?;:" and right.isalpha())):
                text += " "
        text += word
    return text

if __name__ == "__main__":
    print(load_key('language_split_with_space'))
