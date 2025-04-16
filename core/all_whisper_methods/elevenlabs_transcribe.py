import requests
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.config_utils import load_key
from rich import print as rprint
import json
import tempfile
import soundfile as sf
import librosa
import time
from core.all_whisper_methods.audio_preprocess import save_language

# Language code mapping for ElevenLabs API
LANGUAGE_CODE_MAPPING = {
    "bn": "ben",  # Bengali
    "hi": "hin",  # Hindi 
    "ar": "ara",  # Arabic
    "ru": "rus",  # Russian
    "pt": "por",  # Portuguese
    "ja": "jpn",  # Japanese
    "it": "ita",  # Italian
    "de": "deu",  # German
    "fr": "fra",  # French
    "es": "spa",  # Spanish
    "zh": "zho",  # Chinese
    "en": "eng",  # English
}
LANGUAGE_CODE_MAPPING_REVERSE = {v: k for k, v in LANGUAGE_CODE_MAPPING.items()}

def process_transcript(json_data, spacing_threshold=0.3):
    """
    将 elevenlabs 的转录结果解析为按时间顺序的 Whisper 格式
    """
    words_data = json_data.get("words", [])
    
    # 按时间顺序处理单词
    current_segment = None
    segments = []
    
    for item in words_data:
        if item["type"] == "word":
            word_info = {
                "word": item["text"],
                "start": item["start"],
                "end": item["end"]
            }
            
            speaker_id = item.get("speaker_id", "unknown_speaker")
            
            # 如果是新的说话者或者是第一个单词，创建新的 segment
            if not current_segment or current_segment["speaker_id"] != speaker_id:
                if current_segment:
                    segments.append(current_segment)
                current_segment = {
                    "speaker_id": speaker_id,
                    "words": []
                }
            
            current_segment["words"].append(word_info)
            
        elif item["type"] == "spacing" and current_segment and current_segment["words"]:
            # 更新当前段落最后一个单词的结束时间
            spacing_duration = item["end"] - item["start"]
            if spacing_duration < spacing_threshold:
                current_segment["words"][-1]["end"] = item["end"]
    
    # 添加最后一个段落
    if current_segment:
        segments.append(current_segment)
    
    result = {"segments": segments}
    return result

def transcribe_audio_elevenlabs(raw_audio_path: str, vocal_audio_path: str, start: float = None, end: float = None):
    """
    Transcribe audio file to text using ElevenLabs API
    With support for partial audio transcription using start/end timestamps
    """
    rprint(f"[cyan]🎤 Processing audio transcription, file path: {vocal_audio_path}[/cyan]")
    LOG_FILE = f"output/log/elevenlabs_transcribe_{start}_{end}.json"
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # Load audio and process start/end parameters
    y, sr = librosa.load(vocal_audio_path, sr=16000)
    audio_duration = len(y) / sr
    
    if start is None or end is None:
        start = 0
        end = audio_duration
    
    # Slice audio based on start/end
    start_sample = int(start * sr)
    end_sample = int(end * sr)
    y_slice = y[start_sample:end_sample]
    
    # Create temporary file for the sliced audio
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
        temp_filepath = temp_file.name
        sf.write(temp_filepath, y_slice, sr, format='MP3')
    
    try:
        api_key = load_key("whisper.elevenlabs_api_key")
        base_url = "https://api.elevenlabs.io/v1/speech-to-text"
        headers = {"xi-api-key": api_key}
        
        data = {
            "model_id": "scribe_v1",
            "timestamps_granularity": "word",
            "diarize": True,
            "num_speakers": None,
            "tag_audio_events": False
        }
        
        language_code = load_key("whisper.language")
        if language_code not in LANGUAGE_CODE_MAPPING:
            raise ValueError(f"Unsupported language code: {language_code}")
        data["language_code"] = LANGUAGE_CODE_MAPPING.get(language_code)
        
        with open(temp_filepath, 'rb') as audio_file:
            files = {
                "file": (
                    os.path.basename(temp_filepath),
                    audio_file,
                    'audio/mpeg'
                )
            }
            
            start_time = time.time()
            response = requests.post(
                base_url,
                headers=headers,
                data=data,
                files=files
            )
            
        rprint(f"[yellow]API request sent, status code: {response.status_code}[/yellow]")
        
        # Get the response JSON
        result = response.json()

        # save detected language
        language = LANGUAGE_CODE_MAPPING_REVERSE.get(result["language_code"])
        save_language(language)

        # Adjust timestamps for all words by adding the start time
        if start is not None and 'words' in result:
            for word in result['words']:
                if 'start' in word:
                    word['start'] += start
                if 'end' in word:
                    word['end'] += start
        
        rprint(f"[green]✓ Transcription completed in {time.time() - start_time:.2f} seconds[/green]")
        # parse to whisper format
        parsed_result = process_transcript(result)
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(parsed_result, f, indent=4, ensure_ascii=False)
        return parsed_result
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)

if __name__ == "__main__":
    file_path = input("Enter local audio file path (mp3 format): ")
    language = input("Enter language code for transcription (en or zh or other...): ")
    result = transcribe_audio_elevenlabs(file_path, language_code=language)
    print(result)
    
    # Save result to file
    with open("output/transcript.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
