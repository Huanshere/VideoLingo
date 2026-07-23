import os
from ruamel.yaml import YAML
import threading

CONFIG_PATH = 'config.yaml'
lock = threading.Lock()

yaml = YAML()
yaml.preserve_quotes = True

ATLAS_CLOUD_API_BASE = "https://api.atlascloud.ai/v1"
ATLAS_CLOUD_DEFAULT_MODEL = "qwen/qwen3.5-flash"
ATLAS_CLOUD_REASONING_MODEL = "deepseek-ai/deepseek-v4-pro"
ATLAS_CLOUD_ENV_KEYS = ("ATLASCLOUD_API_KEY", "ATLAS_CLOUD_API_KEY")

_PLACEHOLDER_API_KEYS = {
    "",
    "YOUR_API_KEY",
    "YOUR_OPENAI_API_KEY",
    "your_api_key",
    "your_302_api_key",
}


def is_atlascloud_base_url(base_url):
    return "api.atlascloud.ai" in str(base_url or "").lower()


def is_placeholder_api_key(api_key):
    return str(api_key or "").strip() in _PLACEHOLDER_API_KEYS


def get_atlascloud_api_key_from_env():
    for env_key in ATLAS_CLOUD_ENV_KEYS:
        api_key = os.getenv(env_key)
        if api_key:
            return api_key
    return ""


def resolve_api_key(api_key, base_url=None):
    api_key = str(api_key or "").strip()
    if api_key in ATLAS_CLOUD_ENV_KEYS:
        return os.getenv(api_key) or get_atlascloud_api_key_from_env()
    if is_atlascloud_base_url(base_url) and is_placeholder_api_key(api_key):
        return get_atlascloud_api_key_from_env()
    return api_key

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

def update_key(key, new_value):
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

        if isinstance(current, dict) and keys[-1] in current:
            current[keys[-1]] = new_value
            with open(CONFIG_PATH, 'w', encoding='utf-8') as file:
                yaml.dump(data, file)
            return True
        else:
            raise KeyError(f"Key '{keys[-1]}' not found in configuration")
        
# basic utils
def get_joiner(language):
    if language in load_key('language_split_with_space'):
        return " "
    elif language in load_key('language_split_without_space'):
        return ""
    else:
        raise ValueError(f"Unsupported language code: {language}")

if __name__ == "__main__":
    print(load_key('language_split_with_space'))
