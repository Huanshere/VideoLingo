import os
import json
from threading import Lock
import json_repair
from openai import OpenAI
import litellm
from core.utils.config_utils import load_key
from rich import print as rprint
from core.utils.decorator import except_handler

# ------------
# cache gpt response
# ------------

LOCK = Lock()
GPT_LOG_FOLDER = 'output/gpt_log'

def _save_cache(model, prompt, resp_content, resp_type, resp, message=None, log_title="default"):
    with LOCK:
        logs = []
        file = os.path.join(GPT_LOG_FOLDER, f"{log_title}.json")
        os.makedirs(os.path.dirname(file), exist_ok=True)
        if os.path.exists(file):
            with open(file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        logs.append({"model": model, "prompt": prompt, "resp_content": resp_content, "resp_type": resp_type, "resp": resp, "message": message})
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=4)

def _load_cache(prompt, resp_type, log_title):
    with LOCK:
        file = os.path.join(GPT_LOG_FOLDER, f"{log_title}.json")
        if os.path.exists(file):
            with open(file, 'r', encoding='utf-8') as f:
                for item in json.load(f):
                    if item["prompt"] == prompt and item["resp_type"] == resp_type:
                        return item["resp"]
        return False

# ------------
# ask gpt once
# ------------

def _call_openai(model, messages, response_format, base_url, api_key):
    if 'ark' in base_url:
        base_url = "https://ark.cn-beijing.volces.com/api/v3"
    elif 'v1' not in base_url:
        base_url = base_url.strip('/') + '/v1'
    client = OpenAI(api_key=api_key, base_url=base_url)
    params = dict(
        model=model,
        messages=messages,
        response_format=response_format,
        timeout=300
    )
    return client.chat.completions.create(**params)


def _call_litellm(model, messages, response_format, base_url, api_key):
    params = dict(
        model=model,
        messages=messages,
        drop_params=True,
        timeout=300,
    )
    if response_format:
        params["response_format"] = response_format
    if api_key:
        params["api_key"] = api_key
    if base_url:
        params["api_base"] = base_url
    return litellm.completion(**params)


@except_handler("GPT request failed", retry=5)
def ask_gpt(prompt, resp_type=None, valid_def=None, log_title="default"):
    if not load_key("api.key"):
        raise ValueError("API key is not set")
    # check cache
    cached = _load_cache(prompt, resp_type, log_title)
    if cached:
        rprint("use cache response")
        return cached

    model = load_key("api.model")
    base_url = load_key("api.base_url")
    api_key = load_key("api.key")
    response_format = {"type": "json_object"} if resp_type == "json" and load_key("api.llm_support_json") else None

    messages = [{"role": "user", "content": prompt}]

    provider = load_key("api.provider")
    if provider == "litellm":
        resp_raw = _call_litellm(model, messages, response_format, base_url, api_key)
    else:
        resp_raw = _call_openai(model, messages, response_format, base_url, api_key)

    # process and return full result
    resp_content = resp_raw.choices[0].message.content
    if resp_type == "json":
        resp = json_repair.loads(resp_content)
    else:
        resp = resp_content

    # check if the response format is valid
    if valid_def:
        valid_resp = valid_def(resp)
        if valid_resp['status'] != 'success':
            _save_cache(model, prompt, resp_content, resp_type, resp, log_title="error", message=valid_resp['message'])
            raise ValueError(f"API response error: {valid_resp['message']}")

    _save_cache(model, prompt, resp_content, resp_type, resp, log_title=log_title)
    return resp


if __name__ == '__main__':
    from rich import print as rprint

    result = ask_gpt("""test respond ```json\n{\"code\": 200, \"message\": \"success\"}\n```""", resp_type="json")
    rprint(f"Test json output result: {result}")
