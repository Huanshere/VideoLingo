import os, sys, json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *
from threading import Lock
import json_repair
import json 
LOG_FOLDER = 'output/gpt_log'
LOCK = Lock()

def save_log(model, prompt, response, log_title = 'default'):
    os.makedirs(LOG_FOLDER, exist_ok=True)
    log_data = {
        "model": model,
        "prompt": prompt,
        "response": response
    }
    log_file = os.path.join(LOG_FOLDER, f"{log_title}.json")
    
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            logs = json.load(f)
    else:
        logs = []
    logs.append(log_data)
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=4)
        
def check_ask_gpt_history(prompt, model):
    # check if the prompt has been asked before
    if not os.path.exists(LOG_FOLDER):
        return False
    for file_name in os.listdir(LOG_FOLDER):
        if file_name.endswith('.json'):
            file_path = os.path.join(LOG_FOLDER, file_name)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    if item["prompt"] == prompt and item["model"] == model:
                        return item["response"]
    return False

def select_llm(model):
    for config in llm_config:
        if model in config['model'] and config.get('api_key'):
            llm = config
            break
    else:
        raise ValueError(f"⚠️Model <{model}> not found in llm_config or api_key is missing")
    return llm

def ask_gpt(prompt, model = 'deepseek-coder', response_json = True, log_title = 'default'):
    with LOCK:
        if check_ask_gpt_history(prompt, model):
            return check_ask_gpt_history(prompt, model)
    llm = select_llm(model)
    messages = [
        {"role": "user", "content": prompt},
    ]
    from openai import OpenAI
    client = OpenAI(api_key=llm['api_key'], base_url=llm['base_url']+ '/v1')

    response_format = {"type": "json_object"} if response_json and model in llm_support_json else None
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format=response_format
    )
    if response_json:
        try:
            response_data = json_repair.loads(response.choices[0].message.content)
        except:
            print(f"⚠️json_repair failed:\n{response.choices[0].message.content}")
            response_data = response.choices[0].message.content
    else:
        response_data =  response.choices[0].message.content
    
    with LOCK:
        save_log(model, prompt, response_data, log_title=log_title)

    return response_data

# test
if __name__ == '__main__':
    print(ask_gpt('hi there hey response in json format, just simply say 你好.' , model="TA/Qwen/Qwen1.5-110B-Chat", response_json=True)) 



