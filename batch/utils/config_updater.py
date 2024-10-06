import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
import re

def update_config(key, value):
    with open('config.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    pattern = rf"^{re.escape(key)}\s*=.*$"
    replacement = f"{key} = {repr(value)}"
    new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    with open('config.py', 'w', encoding='utf-8') as f:
        f.write(new_content)

def get_config_value(key):
    with open('config.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    pattern = rf"^{re.escape(key)}\s*=\s*(.*)$"
    match = re.search(pattern, content, flags=re.MULTILINE)
    
    if match:
        return eval(match.group(1))
    else:
        return None

if __name__ == "__main__":
    update_config("DISPLAY_LANGUAGE", "auto")