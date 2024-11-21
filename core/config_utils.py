from ruamel.yaml import YAML
from typing import Any
import os, sys
import threading

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CONFIG_PATH = 'config.yaml'
config_lock = threading.Lock()

yaml = YAML()
yaml.preserve_quotes = True

def load_key(key: str) -> Any:
    with config_lock:
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

def update_key(key: str, new_value: Any) -> bool:
    """Update a key in the config file. If the key doesn't exist, it will be created.
    
    Args:
        key: Dot-separated key path (e.g. "llm_models.default_model.key")
        new_value: Value to set
        
    Returns:
        bool: True if successful
    """
    with config_lock:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as file:
            data = yaml.load(file)

        keys = key.split('.')
        current = data
        
        # 遍历除最后一个key外的所有key
        for k in keys[:-1]:
            # 如果key不存在，创建一个新的字典
            if k not in current:
                current[k] = {}
            current = current[k]
                
        # 设置最终的值
        current[keys[-1]] = new_value
        
        # 保存更新后的配置
        with open(CONFIG_PATH, 'w', encoding='utf-8') as file:
            yaml.dump(data, file)
        return True

        
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
