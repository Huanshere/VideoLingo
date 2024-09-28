import requests
from pathlib import Path
import os, sys
from rich import print as rprint
from moviepy.editor import AudioFileClip
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def fish_tts(text, save_path):
    from config import FISH_TTS_API_KEY, FISH_TTS_CHARACTER, FISH_TTS_CHARACTER_ID_DICT
    if FISH_TTS_CHARACTER not in FISH_TTS_CHARACTER_ID_DICT:
        raise ValueError(f"Character '{FISH_TTS_CHARACTER}' not found in FISH_TTS_CHARACTER_ID_DICT")
    id = FISH_TTS_CHARACTER_ID_DICT[FISH_TTS_CHARACTER]
    url = "https://api.fish.audio/v1/tts"

    payload = {
        "text": text,
        "format": "mp3",
        "mp3_bitrate": 128,
        "normalize": True,
        "reference_id": id
    }
    headers = {
        "Authorization": f"Bearer {FISH_TTS_API_KEY}",
        "Content-Type": "application/json"
    }

    max_retries = 2
    for attempt in range(max_retries):
        response = requests.request("POST", url, json=payload, headers=headers)
        if response.status_code == 200:
            wav_file_path = Path(save_path).with_suffix('.wav')
            wav_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Save the MP3 content to a temporary file
            temp_mp3_path = wav_file_path.with_suffix('.mp3')
            with open(temp_mp3_path, 'wb') as temp_file:
                temp_file.write(response.content)

            # Convert mp3 to wav using moviepy
            audio_clip = AudioFileClip(str(temp_mp3_path))
            audio_clip.write_audiofile(str(wav_file_path))
            audio_clip.close()

            # Remove the temporary MP3 file
            os.remove(temp_mp3_path)

            rprint(f"[bold green]Converted audio saved to {wav_file_path}[/bold green]")
            break
        else:
            rprint(f"[bold red]Request failed, status code: {response.status_code}, retry attempt: {attempt + 1}/{max_retries}[/bold red]")
            if attempt == max_retries - 1:
                rprint("[bold red]Max retry attempts reached, operation failed.[/bold red]")

if __name__ == '__main__':
    fish_tts("今天是个好日子，适合做点人们喜欢的东西！", "test.wav")
