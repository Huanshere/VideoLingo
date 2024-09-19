import os, sys, json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *
from threading import Lock
import json_repair
import json 
from openai import OpenAI
import time
from requests.exceptions import RequestException

LOG_FOLDER = 'output/gpt_log'
LOCK = Lock()

def save_log(model, prompt, response, log_title = 'default', message = None):
    os.makedirs(LOG_FOLDER, exist_ok=True)
    log_data = {
        "model": model,
        "prompt": prompt,
        "response": response,
        "message": message
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
        # check all files in the folder except error.json
        if file_name.endswith('.json') and "error" not in file_name:
            file_path = os.path.join(LOG_FOLDER, file_name)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    if item["prompt"] == prompt and item["model"] == model:
                        return item["response"]
    return False

def select_llm(model):
    from config import MODEL, API_KEY, BASE_URL
    if model in MODEL and API_KEY:
        return {'api_key': API_KEY, 'base_url': BASE_URL, 'model': MODEL}
    else:
        print(f"{model} {MODEL}")
        raise ValueError(f"⚠️Model <{model}> not found in MODEL or API_KEY is missing")

def make_api_call(client, model, messages, response_format):
    return client.chat.completions.create(
        model=model,
        messages=messages,
        response_format=response_format
    )

def ask_gpt(prompt, model, response_json=True ,valid_def=None, log_title='default'):
    with LOCK:
        if check_ask_gpt_history(prompt, model):
            return check_ask_gpt_history(prompt, model)
    llm = select_llm(model)
    messages = [
        {"role": "user", "content": prompt},
    ]
    
    base_url = llm['base_url'].strip('/') + '/v1' if 'v1' not in llm['base_url'] else llm['base_url']
    client = OpenAI(api_key=llm['api_key'], base_url=base_url)
    from config import llm_support_json
    response_format = {"type": "json_object"} if response_json and model in llm_support_json else None
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = make_api_call(client, model, messages, response_format)
            
            if response_json:
                try:
                    response_data = json_repair.loads(response.choices[0].message.content)
                    
                    # check if the response is valid, otherwise save the log and raise error and retry
                    if valid_def:
                        valid_response = valid_def(response_data)
                        if valid_response['status'] != 'success':
                            save_log(model, prompt, response_data, log_title="error", message=valid_response['message'])
                            raise ValueError(f"❎ API response error: {valid_response['message']}")
                        
                    break  # Successfully accessed and parsed, break the loop
                except Exception as e:
                    response_data = response.choices[0].message.content
                    print(f"❎ json_repair parsing failed. Retrying: '''{response_data}'''")
                    save_log(model, prompt, response_data, log_title="error", message=f"json_repair parsing failed.")
                    if attempt == max_retries - 1:
                        raise Exception(f"JSON parsing still failed after {max_retries} attempts: {e}")
            else:
                response_data = response.choices[0].message.content
                break  # Non-JSON format, break the loop directly
                
        except RequestException as e:
            if attempt < max_retries - 1:
                print(f"Request error: {e}. Retrying ({attempt + 1}/{max_retries})...")
                time.sleep(2)
            else:
                raise Exception(f"Still failed after {max_retries} attempts: {e}")
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Unexpected error occurred: {e}\nRetrying...")
                time.sleep(2)
            else:
                raise Exception(f"Still failed after {max_retries} attempts: {e}")
    with LOCK:
        if log_title != 'None':
            save_log(model, prompt, response_data, log_title=log_title)

    return response_data

# test
if __name__ == '__main__':
    from config import step3_2_split_model
    print(ask_gpt('hi there hey response in json format, just simply say 你好.' , model=step3_2_split_model, response_json=True))