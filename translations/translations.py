import json

DISPLAY_LANGUAGES = {
    "🇬🇧 English": "en",
    "🇨🇳 简体中文": "zh-CN",
    "🇭🇰 繁体中文": "zh-HK",
    "🇯🇵 日本語": "ja",
    "🇪🇸 Español": "es",
    "🇷🇺 Русский": "ru",
    "🇫🇷 Français": "fr",
    "🇸🇪 Svenska": "sv",
}

SUPPORTED_LANGUAGES = set(DISPLAY_LANGUAGES.values())


def normalize_language_code(language):
    if not language:
        return None

    code = str(language).replace("_", "-").lower()
    if code in {"zh", "zh-cn", "zh-hans", "zh-sg"}:
        return "zh-CN"
    if code in {"zh-hk", "zh-tw", "zh-mo", "zh-hant"}:
        return "zh-HK"

    base_code = code.split("-")[0]
    if base_code in SUPPORTED_LANGUAGES:
        return base_code
    return None


def _language_from_accept_language(header):
    for item in (header or "").split(","):
        code = normalize_language_code(item.split(";")[0].strip())
        if code:
            return code
    return None


def _config_language():
    try:
        from core.utils.config_utils import load_key

        return normalize_language_code(load_key("display_language"))
    except Exception:
        return None


def _streamlit_language():
    try:
        import streamlit as st

        if "_display_language" in st.session_state:
            return normalize_language_code(st.session_state["_display_language"])

        query_language = st.query_params.get("lang")
        if isinstance(query_language, list):
            query_language = query_language[0] if query_language else None
        query_language = normalize_language_code(query_language)
        if query_language:
            return query_language

        return _language_from_accept_language(st.context.headers.get("accept-language", ""))
    except Exception:
        return None


def get_current_language(default="en"):
    return _streamlit_language() or _config_language() or default


def init_display_language():
    language = get_current_language(default="en")
    try:
        import streamlit as st

        st.session_state.setdefault("_display_language", language)
    except Exception:
        pass
    return language


def set_display_language(language):
    language = normalize_language_code(language) or "en"
    try:
        import streamlit as st

        st.session_state["_display_language"] = language
        st.query_params["lang"] = language
    except Exception:
        pass
    try:
        from core.utils.config_utils import update_key

        update_key("display_language", language)
    except Exception:
        pass
    return language

# Load the language file based on user selection
def load_translations(language="en"):
    with open(f'translations/{language}.json', 'r', encoding='utf-8') as file:
        return json.load(file)

# Function to fetch the translation
def translate(key):
    try:
        display_language = get_current_language()
        translations = load_translations(display_language)
        translation = translations.get(key)
        if translation is None:
            print(f"Warning: Translation not found for key '{key}' in language '{display_language}'")
            return key
        return translation
    except:
        return key
