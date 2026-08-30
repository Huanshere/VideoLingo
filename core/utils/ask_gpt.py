import os
import json
from threading import Lock
import json_repair
from openai import OpenAI
from core.utils.config_utils import load_key
from rich import print as rprint
from core.utils.decorator import NonRetryableError, except_handler

# ------------
# cache gpt response
# ------------

LOCK = Lock()
USAGE_LOCK = Lock()
GPT_LOG_FOLDER = 'output/gpt_log'
USAGE_FILE = os.path.join(GPT_LOG_FOLDER, 'usage.json')


def _load_optional_key(key, default):
    try:
        return load_key(key)
    except KeyError:
        return default


def _load_usage():
    if not os.path.exists(USAGE_FILE):
        return {'requests': 0, 'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
    with open(USAGE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def _check_usage_limit():
    max_tokens = int(_load_optional_key('api.max_total_tokens', 0) or 0)
    with USAGE_LOCK:
        total_tokens = int(_load_usage().get('total_tokens', 0))
    if max_tokens > 0 and total_tokens >= max_tokens:
        raise NonRetryableError(
            f"LLM token limit reached: {total_tokens} >= {max_tokens}. "
            "Increase api.max_total_tokens or set it to 0 to continue."
        )


def _record_usage(usage, log_title):
    if usage is None:
        return None
    with USAGE_LOCK:
        totals = _load_usage()
        prompt_tokens = int(getattr(usage, 'prompt_tokens', 0) or 0)
        completion_tokens = int(getattr(usage, 'completion_tokens', 0) or 0)
        total_tokens = int(getattr(usage, 'total_tokens', 0) or prompt_tokens + completion_tokens)
        totals['requests'] = int(totals.get('requests', 0)) + 1
        totals['prompt_tokens'] = int(totals.get('prompt_tokens', 0)) + prompt_tokens
        totals['completion_tokens'] = int(totals.get('completion_tokens', 0)) + completion_tokens
        totals['total_tokens'] = int(totals.get('total_tokens', 0)) + total_tokens
        stages = totals.setdefault('stages', {})
        stage = stages.setdefault(log_title, {'requests': 0, 'total_tokens': 0})
        stage['requests'] += 1
        stage['total_tokens'] += total_tokens
        os.makedirs(GPT_LOG_FOLDER, exist_ok=True)
        with open(USAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(totals, f, ensure_ascii=False, indent=2)
        return totals


def _deepseek_extra_body(base_url):
    if 'api.deepseek.com' not in base_url:
        return None
    thinking = _load_optional_key('api.thinking', 'disabled')
    return {'thinking': {'type': thinking}}

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

@except_handler("GPT request failed", retry=5)
def ask_gpt(prompt, resp_type=None, valid_def=None, log_title="default"):
    if not load_key("api.key"):
        raise ValueError("API key is not set")
    # check cache
    cached = _load_cache(prompt, resp_type, log_title)
    if cached:
        rprint("use cache response")
        return cached

    _check_usage_limit()

    model = load_key("api.model")
    base_url = load_key("api.base_url")
    if 'ark' in base_url:
        base_url = "https://ark.cn-beijing.volces.com/api/v3" # huoshan base url
    elif 'v1' not in base_url:
        base_url = base_url.strip('/') + '/v1'
    client = OpenAI(api_key=load_key("api.key"), base_url=base_url)
    response_format = {"type": "json_object"} if resp_type == "json" and load_key("api.llm_support_json") else None

    messages = [{"role": "user", "content": prompt}]

    params = dict(
        model=model,
        messages=messages,
        response_format=response_format,
        timeout=300
    )
    extra_body = _deepseek_extra_body(base_url)
    if extra_body:
        params['extra_body'] = extra_body
    resp_raw = client.chat.completions.create(**params)
    usage = _record_usage(getattr(resp_raw, 'usage', None), log_title)
    if usage:
        rprint(
            f"[cyan]LLM usage: {usage['requests']} requests, "
            f"{usage['total_tokens']} total tokens[/cyan]"
        )

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
            raise ValueError(f"❎ API response error: {valid_resp['message']}")

    _save_cache(model, prompt, resp_content, resp_type, resp, log_title=log_title)
    return resp


if __name__ == '__main__':
    from rich import print as rprint
    
    result = ask_gpt("""test respond ```json\n{\"code\": 200, \"message\": \"success\"}\n```""", resp_type="json")
    rprint(f"Test json output result: {result}")
