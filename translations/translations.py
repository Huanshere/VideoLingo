import json
from core.utils import load_key

DISPLAY_LANGUAGES = {
    "🇬🇧 English": "en",
    "🇨🇳 简体中文": "zh-CN",
    "🇭🇰 繁体中文": "zh-HK",
    "🇯🇵 日本語": "ja",
    "🇪🇸 Español": "es",
    "🇷🇺 Русский": "ru",
    "🇫🇷 Français": "fr",
}

# Load the language file based on user selection
def load_translations(language="en"):
    with open(f'translations/{language}.json', 'r', encoding='utf-8') as file:
        return json.load(file)

# Function to fetch the translation
def translate(key):
    try:
        display_language = load_key("display_language")
        translations = load_translations(display_language)
        translation = translations.get(key)
        if translation is None:
            print(f"Warning: Translation not found for key '{key}' in language '{display_language}'")
            return key
        return translation
    except:
        return key
