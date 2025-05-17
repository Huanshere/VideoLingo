import os
import json
import time
import requests
from rich import print as rprint
from core.utils import *

# ----------------------------------------
# ISO 639-2 to 1
# ----------------------------------------

iso_639_2_to_1 = {
    "eng": "en",
    "fra": "fr", 
    "deu": "de",
    "ita": "it",
    "spa": "es",
    "rus": "ru",
    "kor": "ko",
    "jpn": "ja",
    "zho": "zh",
    "yue": "zh"
}

# ----------------------------
# elevenlabs format to whisper format
# ----------------------------

SPLIT_GAP = 1
def elev2whisper(elev_json, word_level_timestamp = False):
    words = elev_json.get("words", [])
    if not words:
        return {"segments": []}

    segments, seg = [], {
        "text": "",                     # accumulated text
        "start": words[0]["start"],     # seg start time
        "end": words[0]["end"],         # seg end time (updates)
        "speaker": words[0]["speaker_id"],
        "words": []                       # optional per‑word info
    }

    for prev, nxt in zip(words, words[1:] + [None]):  # pairwise with sentinel
        seg["text"] += prev["text"]
        seg["end"] = prev["end"]
        if word_level_timestamp:
            seg["words"].append({"text": prev["text"], "start": prev["start"], "end": prev["end"]})
        # decide whether to break the segment
        if nxt is None or (nxt["start"] - prev["end"] > SPLIT_GAP) or (nxt["speaker_id"] != seg["speaker"]):
            seg["text"] = seg["text"].strip()
            if not word_level_timestamp:
                seg.pop("words")
            segments.append(seg)
            if nxt is not None:  # seed next segment
                seg = {
                    "text": "",
                    "start": nxt["start"],
                    "end": nxt["end"],
                    "speaker": nxt["speaker_id"],
                    "words": []
                }
    return {"segments": segments}

@except_handler("failed to transcribe audio with elevenlabs", retry=2)
def transcribe_audio_elevenlabs(raw_audio_path, vocal_audio_path):
    rprint(f"[cyan]🎤 Processing audio transcription, file path: {vocal_audio_path}[/cyan]")
    LOG_FILE = f"output/log/elevenlabs_transcribe.json"
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    
    api_key = load_key("whisper.elevenlabs_api_key")
    base_url = "https://api.elevenlabs.io/v1/speech-to-text"
    headers = {"xi-api-key": api_key}
    
    data = {
        "model_id": "scribe_v1",
        "timestamps_granularity": "word",
        "language_code": load_key("whisper.language"),
        "diarize": True,
        "num_speakers": None,
        "tag_audio_events": False
    }
    
    with open(vocal_audio_path, 'rb') as audio_file:
        files = {"file": (os.path.basename(vocal_audio_path), audio_file, 'audio/mpeg')}
        start_time = time.time()
        response = requests.post(base_url, headers=headers, data=data, files=files)
        
    rprint(f"[yellow]API request sent, status code: {response.status_code}[/yellow]")
    result = response.json()

    # save detected language
    detected_language = iso_639_2_to_1.get(result["language_code"], result["language_code"])
    update_key("whisper.detected_language", detected_language)
    
    rprint(f"[green]✓ Transcription completed in {time.time() - start_time:.2f} seconds[/green]")
    parsed_result = elev2whisper(result)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(parsed_result, f, indent=4, ensure_ascii=False)
    return parsed_result

if __name__ == "__main__":
    file_path = input("Enter local audio file path (mp3 format): ")
    language = input("Enter language code for transcription (en or zh or other...): ")
    result = transcribe_audio_elevenlabs(file_path, language_code=language)
    print(result)
    
    # Save result to file
    with open("output/transcript.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
