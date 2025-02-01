import json

# Load the language file based on user selection
def load_translations(language="en"):
    with open(f'translations/{language}.json', 'r') as file:
        return json.load(file)

# Function to fetch the translation
def translate(key, language="en"):
    translations = load_translations(language)
    translation = translations.get(key)
    if translation is None:
        print(f"Warning: Translation not found for key '{key}' in language '{language}'")
        return key
    return translation
