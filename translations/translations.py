import json
import sys,os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config_utils import load_key

# Load the language file based on user selection
def load_translations(language="en"):
    with open(f'translations/{language}.json', 'r', encoding='utf-8') as file:
        return json.load(file)

# Function to fetch the translation
def translate(key):
    display_language = load_key("display_language")
    translations = load_translations(display_language)
    translation = translations.get(key)
    if translation is None:
        print(f"Warning: Translation not found for key '{key}' in language '{display_language}'")
        return key
    return translation
