import os, subprocess
import pandas as pd
from typing import Dict
from pydub import AudioSegment
from core.utils import *
from core.utils.models import *
from pydub import AudioSegment
from rich import print as rprint

def normalize_audio_volume(audio_path, output_path, target_db = -20.0, format = "wav"):
    audio = AudioSegment.from_file(audio_path)
    change_in_dBFS = target_db - audio.dBFS
    normalized_audio = audio.apply_gain(change_in_dBFS)
    normalized_audio.export(output_path, format=format)
    rprint(f"[green]✅ Audio normalized from {audio.dBFS:.1f}dB to {target_db:.1f}dB[/green]")
    return output_path

def convert_video_to_audio(video_file: str):
    os.makedirs(_AUDIO_DIR, exist_ok=True)
    if not os.path.exists(_RAW_AUDIO_FILE):
        rprint(f"[blue]🎬➡️🎵 Converting to high quality audio with FFmpeg ......[/blue]")
        subprocess.run([
            'ffmpeg', '-y', '-i', video_file, '-vn',
            '-c:a', 'libmp3lame', '-b:a', '32k','-ar', '16000','-ac', '1', 
            '-metadata', 'encoding=UTF-8', _RAW_AUDIO_FILE
        ], check=True, stderr=subprocess.PIPE)
        rprint(f"[green]🎬➡️🎵 Converted <{video_file}> to <{_RAW_AUDIO_FILE}> with FFmpeg\n[/green]")

@except_handler("Failed to get audio duration")
def get_audio_duration(audio_file: str) -> float:
    """Get the duration of an audio file using pydub."""
    audio = AudioSegment.from_file(audio_file)
    duration = len(audio) / 1000.0  # 转换毫秒为秒
    return duration

def process_transcription(result: Dict) -> pd.DataFrame:
    all_words = []
    for segment in result['segments']:
        # Get speaker, if not exists, set to None
        speaker = segment.get('speaker', None)
        
        for word in segment['words']:
            # Check word length
            if len(word["word"]) > 30:
                rprint(f"[yellow]⚠️ Warning: Detected word longer than 30 characters, skipping: {word['word']}[/yellow]")
                continue
                
            # ! For French, we need to convert guillemets to empty strings
            word["word"] = word["word"].replace('»', '').replace('«', '')
            
            if 'start' not in word and 'end' not in word:
                if all_words:
                    # Assign the end time of the previous word as the start and end time of the current word
                    word_dict = {
                        'text': word["word"],
                        'start': all_words[-1]['end'],
                        'end': all_words[-1]['end'],
                        'speaker': speaker
                    }
                    all_words.append(word_dict)
                else:
                    # If it's the first word, look next for a timestamp then assign it to the current word
                    next_word = next((w for w in segment['words'] if 'start' in w and 'end' in w), None)
                    if next_word:
                        word_dict = {
                            'text': word["word"],
                            'start': next_word["start"],
                            'end': next_word["end"],
                            'speaker': speaker
                        }
                        all_words.append(word_dict)
                    else:
                        raise Exception(f"No next word with timestamp found for the current word : {word}")
            else:
                # Normal case, with start and end times
                word_dict = {
                    'text': f'{word["word"]}',
                    'start': word.get('start', all_words[-1]['end'] if all_words else 0),
                    'end': word['end'],
                    'speaker': speaker
                }
                
                all_words.append(word_dict)
    
    return pd.DataFrame(all_words)

def save_results(df: pd.DataFrame):
    os.makedirs('output/log', exist_ok=True)

    # Remove rows where 'text' is empty
    initial_rows = len(df)
    df = df[df['text'].str.len() > 0]
    removed_rows = initial_rows - len(df)
    if removed_rows > 0:
        rprint(f"[blue]ℹ️ Removed {removed_rows} row(s) with empty text.[/blue]")
    
    # Check for and remove words longer than 20 characters
    long_words = df[df['text'].str.len() > 30]
    if not long_words.empty:
        rprint(f"[yellow]⚠️ Warning: Detected {len(long_words)} word(s) longer than 30 characters. These will be removed.[/yellow]")
        df = df[df['text'].str.len() <= 30]
    
    df['text'] = df['text'].apply(lambda x: f'"{x}"')
    df.to_excel(_2_CLEANED_CHUNKS, index=False)
    rprint(f"[green]📊 Excel file saved to {_2_CLEANED_CHUNKS}[/green]")

def save_language(language: str):
    update_key("whisper.detected_language", language)