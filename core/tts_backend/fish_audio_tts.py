import io
import os
import re
import struct
from pathlib import Path

import msgpack
import requests
from pydub import AudioSegment

from core.utils import *
from core.utils.models import _AUDIO_REFERS_DIR

API_URL = "https://api.fish.audio/v1/tts"
DEFAULT_MODEL = "s2.1-pro"
MODES = ("clone", "preset")
VOICE_ID = re.compile(r"[0-9a-f]{32}")
# Fish Audio recommends 10-30 s of clear speech of one speaker as the reference
MIN_REFERENCE_SECONDS = 15
MAX_REFERENCE_SECONDS = 30


def _wav_bytes(audio):
    buffer = io.BytesIO()
    audio.set_channels(1).export(buffer, format="wav")
    return buffer.getvalue()


def stable_reference(task_df):
    """The first lines of the video as one reference for all lines: (WAV bytes, the text spoken in it)."""
    audio, texts = AudioSegment.empty(), []
    for _, row in task_df.iterrows():
        path = os.path.join(_AUDIO_REFERS_DIR, f"{row['number']}.wav")
        if not os.path.exists(path):
            continue
        clip = AudioSegment.from_file(path)
        if len(audio) + len(clip) > MAX_REFERENCE_SECONDS * 1000:
            if not texts:  # one line that is longer than the limit
                audio, texts = clip[:MAX_REFERENCE_SECONDS * 1000], [str(row['origin'])]
            break
        audio += clip
        texts.append(str(row['origin']))
        if len(audio) >= MIN_REFERENCE_SECONDS * 1000:
            break
    if not texts:
        raise FileNotFoundError(f"No reference audio of the video in {_AUDIO_REFERS_DIR}")
    return _wav_bytes(audio), " ".join(texts)


def voice_id_of(value):
    """The ID of a voice, from the ID itself or from the address of its page on fish.audio."""
    value = str(value or "").strip()
    found = VOICE_ID.search(value.lower())
    return found.group() if found else value


def _with_length(wav):
    """The WAV is streamed, its header has no real length: write the length into it."""
    data = wav.find(b"data", 12, 200)
    if wav[:4] != b"RIFF" or data < 0:
        return wav
    return (wav[:4] + struct.pack("<I", len(wav) - 8) + wav[8:data + 4]
            + struct.pack("<I", len(wav) - data - 8) + wav[data + 8:])


@except_handler("Failed to generate audio using Fish Audio", retry=3, delay=1)
def fish_audio_tts(text, save_as, number=None, task_df=None):
    settings = load_key("fish_audio")
    mode = settings.get("mode") or "clone"
    if mode not in MODES:
        raise ValueError(f"Invalid Fish Audio mode: {mode}. Please choose from {MODES}")
    api_key = str(settings.get("api_key") or "")
    if not api_key or api_key.startswith("YOUR_"):
        raise ValueError("Fish Audio: the API key is missing (fish_audio.api_key)")
    payload = {"text": text, "format": "wav", "normalize": True, "latency": "normal"}
    if mode == "preset":
        payload["reference_id"] = voice_id_of(settings.get("voice_id"))
        if not payload["reference_id"]:
            raise ValueError("Fish Audio: the mode `preset` needs a voice id (fish_audio.voice_id)")
    else:
        audio, reference_text = stable_reference(task_df)
        payload["references"] = [{"audio": audio, "text": reference_text}]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/msgpack",  # JSON cannot carry the reference audio
        "model": settings.get("model") or DEFAULT_MODEL,
    }
    response = requests.post(API_URL, headers=headers, data=msgpack.packb(payload, use_bin_type=True), timeout=180)
    if response.status_code != 200:
        raise ValueError(f"Fish Audio request failed: HTTP {response.status_code} {response.text[:200]}")
    if len(response.content) <= 44:
        raise ValueError(f"Fish Audio request failed: HTTP 200 without audio ({len(response.content)} bytes)")

    Path(save_as).parent.mkdir(parents=True, exist_ok=True)
    with open(save_as, "wb") as f:
        f.write(_with_length(response.content))
    print(f"Audio saved to {save_as}")


if __name__ == "__main__":
    import pandas as pd
    from core.utils.models import _8_1_AUDIO_TASK
    fish_audio_tts("你好，欢迎使用 VideoLingo！", "test.wav", 1, pd.read_excel(_8_1_AUDIO_TASK))
