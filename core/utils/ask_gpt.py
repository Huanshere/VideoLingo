import os
import re
import json
import ipaddress
from threading import Lock
from urllib.parse import urlparse
import json_repair
from openai import OpenAI
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
# api key
# ------------

LOCAL_API_KEY = "not-needed"  # the OpenAI client refuses an empty key; local servers ignore it

def is_local_endpoint(base_url):
    """Ollama, LM Studio, vLLM... on this machine or the private network need no API key."""
    host = (urlparse(base_url if "//" in str(base_url) else f"//{base_url}").hostname or "").lower()
    if host in ("localhost", "host.docker.internal") or host.endswith((".local", ".localhost")):
        return True
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    return address.is_loopback or address.is_private or address.is_unspecified

def get_api_key():
    key = load_key("api.key")
    if key:
        return key
    if is_local_endpoint(load_key("api.base_url")):
        return LOCAL_API_KEY
    raise ValueError("API key is not set")

# ------------
# base url
# ------------

def normalize_base_url(base_url):
    """Accept the forms people paste: with or without /v1, or the full chat completions URL."""
    base_url = str(base_url or "").strip()
    if 'ark' in base_url:
        return "https://ark.cn-beijing.volces.com/api/v3" # huoshan base url
    base_url = re.sub(r'/chat/completions/?$', '', base_url.rstrip('/'))
    if 'v1' not in base_url and not re.search(r'/v\d+$', base_url):  # e.g. .../api/paas/v4
        base_url = base_url.strip('/') + '/v1'
    return base_url

# ------------
# parse json response
# ------------

def parse_json_response(resp_content):
    """Read the JSON object of a reply that may carry reasoning or prose around it."""
    text = re.sub(r'<think>.*?</think>', '', resp_content or '', flags=re.DOTALL | re.IGNORECASE)
    text = re.split(r'</think>', text, flags=re.IGNORECASE)[-1]  # opening tag cut off by the server
    text = re.sub(r'<think>.*', '', text, flags=re.DOTALL | re.IGNORECASE)  # reasoning never closed
    blocks = re.findall(r'```(?:json)?[ \t]*\n(.*?)```', text, flags=re.DOTALL | re.IGNORECASE)
    candidates = [block for block in reversed(blocks) if '{' in block] + [text]
    resp = None
    for candidate in candidates:
        resp = json_repair.loads(candidate)
        if isinstance(resp, list):  # prose with several braces: the answer is the last object
            resp = next((item for item in reversed(resp) if isinstance(item, dict)), resp)
        if isinstance(resp, dict) and resp:
            return resp
    raise ValueError(f"❎ API response is not a JSON object: {str(resp_content)[:200]!r}")

# ------------
# ask gpt once
# ------------

@except_handler("GPT request failed", retry=5)
def ask_gpt(prompt, resp_type=None, valid_def=None, log_title="default"):
    api_key = get_api_key()
    # check cache
    cached = _load_cache(prompt, resp_type, log_title)
    if cached:
        rprint("use cache response")
        return cached

    model = load_key("api.model")
    base_url = normalize_base_url(load_key("api.base_url"))
    client = OpenAI(api_key=api_key, base_url=base_url)
    response_format = {"type": "json_object"} if resp_type == "json" and load_key("api.llm_support_json") else None

    messages = [{"role": "user", "content": prompt}]

    params = dict(
        model=model,
        messages=messages,
        timeout=300
    )
    if response_format is not None:
        params["response_format"] = response_format
    resp_raw = client.chat.completions.create(**params)

    # process and return full result
    resp_content = resp_raw.choices[0].message.content
    if resp_type == "json":
        try:
            resp = parse_json_response(resp_content)
        except ValueError as e:
            _save_cache(model, prompt, resp_content, resp_type, None, log_title="error", message=str(e))
            raise
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
