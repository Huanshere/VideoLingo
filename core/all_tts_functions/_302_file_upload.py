import requests
import os, sys
import json
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from core.config_utils import load_key

#! This is only for `_302_f5tts.py`
def upload_file_to_302(file_path):
    """Upload a file to 302.ai API and return the URL if successful."""
    try:
        API_KEY = load_key("f5tts.api_key")
        url = "https://api.302.ai/302/upload-file"
        
        files = [('file', (os.path.basename(file_path), open(file_path, 'rb'), 'application/octet-stream'))]
        headers = {'Authorization': f'Bearer {API_KEY}'}
        
        response = requests.request("POST", url, headers=headers, data={}, files=files)
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                if response_data.get('code') == 200:
                    return response_data.get('data')
                else:
                    raise Exception(f"API error: {response_data.get('message', 'Unknown error')}")
            except json.JSONDecodeError:
                raise Exception("Response was not valid JSON")
        else:
            raise Exception(f"Upload failed with status code: {response.status_code}")
            
    except Exception as e:
        raise e

if __name__ == "__main__":
    url = upload_file_to_302("README.md")
    print(url)