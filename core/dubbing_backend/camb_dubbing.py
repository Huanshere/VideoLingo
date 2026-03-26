import time
import requests
from pathlib import Path
from rich import print as rprint
from core.utils import load_key

CAMB_API_BASE = "https://client.camb.ai/apis"

# Numeric language IDs for dubbing/translation endpoints
CAMB_LANGUAGE_IDS = {
    "English (US)": 1,
    "Spanish (Spain)": 54,
    "French (France)": 76,
    "German": 31,
    "Japanese": 88,
    "Hindi": 81,
    "Portuguese (Brazil)": 111,
    "Chinese (Mandarin)": 139,
    "Korean": 94,
    "Italian": 86,
    "Dutch": 115,
    "Russian": 46,
    "Arabic": 50,
}

def _headers():
    api_key = load_key("camb_dubbing.api_key")
    return {
        "x-api-key": api_key,
        "Content-Type": "application/json",
    }

def create_dubbing_task(video_url, source_language_id, target_language_ids):
    """Submit a dubbing task to CAMB AI. Returns task_id."""
    payload = {
        "video_url": video_url,
        "source_language": source_language_id,
        "target_languages": target_language_ids,
    }
    response = requests.post(f"{CAMB_API_BASE}/dub", headers=_headers(), json=payload)
    if response.status_code != 200:
        raise RuntimeError(f"CAMB dubbing task creation failed: {response.status_code} - {response.text}")
    task_id = response.json()["task_id"]
    rprint(f"[green]CAMB dubbing task created: {task_id}[/green]")
    return task_id

def poll_dubbing_status(task_id, poll_interval=5, timeout=600):
    """Poll dubbing task until completion. Returns run_id on success."""
    elapsed = 0
    while elapsed < timeout:
        response = requests.get(f"{CAMB_API_BASE}/dub/{task_id}", headers=_headers())
        if response.status_code != 200:
            raise RuntimeError(f"Failed to get dubbing status: {response.status_code} - {response.text}")
        data = response.json()
        status = data.get("status", "UNKNOWN")
        rprint(f"[cyan]Dubbing status: {status} ({elapsed}s elapsed)[/cyan]")

        if status == "SUCCESS":
            return data.get("run_id")
        elif status in ("ERROR", "FAILED", "TIMEOUT"):
            raise RuntimeError(f"CAMB dubbing failed with status: {status}. Full response: {data}")

        time.sleep(poll_interval)
        elapsed += poll_interval

    raise TimeoutError(f"CAMB dubbing timed out after {timeout}s")

def download_dubbing_result(run_id, save_path):
    """Download the dubbed video result."""
    response = requests.get(f"{CAMB_API_BASE}/dub-result/{run_id}", headers=_headers())
    if response.status_code != 200:
        raise RuntimeError(f"Failed to get dubbing result: {response.status_code} - {response.text}")

    data = response.json()
    video_url = data.get("video_url")
    if not video_url:
        raise RuntimeError(f"No video_url in dubbing result: {data}")

    # Download the actual video file from the signed URL
    rprint(f"[cyan]Downloading dubbed video...[/cyan]")
    video_response = requests.get(video_url)
    if video_response.status_code != 200:
        raise RuntimeError(f"Failed to download dubbed video: {video_response.status_code}")

    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)

    with open(save_path, "wb") as f:
        f.write(video_response.content)
    rprint(f"[green]Dubbed video saved to {save_path} ({len(video_response.content):,} bytes)[/green]")
    return str(save_path)

def camb_dub(video_url, source_language_id, target_language_ids, save_path, poll_interval=5, timeout=600):
    """End-to-end dubbing: submit, poll, download."""
    task_id = create_dubbing_task(video_url, source_language_id, target_language_ids)
    run_id = poll_dubbing_status(task_id, poll_interval=poll_interval, timeout=timeout)
    return download_dubbing_result(run_id, save_path)

if __name__ == "__main__":
    # Quick test - requires a publicly accessible video URL
    result = camb_dub(
        video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        source_language_id=1,
        target_language_ids=[54],
        save_path="test_dubbed.mp4",
    )
    print(f"Result: {result}")
