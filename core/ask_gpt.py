import os, sys, json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *
from threading import Lock
import json_repair
import json 
from openai import OpenAI
from httpx import HTTPStatusError
import time
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
    if model in llm_config['model'] and llm_config.get('api_key'):
        return llm_config
    else:
        print(f"{model} {llm_config}")
        raise ValueError(f"⚠️Model <{model}> 在 llm_config 中未找到或缺少 api_key")

def ask_gpt(prompt, model, response_json = True, log_title = 'default'):
    with LOCK:
        if check_ask_gpt_history(prompt, model):
            return check_ask_gpt_history(prompt, model)
    llm = select_llm(model)
    messages = [
        {"role": "user", "content": prompt},
    ]
    
    
    client = OpenAI(api_key=llm['api_key'], base_url=llm['base_url']+ '/v1')
    response_format = {"type": "json_object"} if response_json and model in llm_support_json else None
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                response_format=response_format
            )
        except HTTPStatusError as e:
            if attempt < max_retries - 1:
                print(f"HTTP错误: {e}. 正在重试 ({attempt + 1}/{max_retries})...")
                time.sleep(1)
            else:
                raise Exception(f"在{max_retries}次尝试后仍然失败: {e}")
        except Exception as e:
            print(f"发生未预期的错误: {e}\n正在重试...")
            time.sleep(1)
        
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
    print(ask_gpt('hi there hey response in json format, just simply say 你好.' , model='claude-3-5-sonnet-20240620', response_json=True)) 



