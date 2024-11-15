import os, sys, subprocess
import pandas as pd
from typing import Dict, List, Tuple
from rich import print
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.config_utils import update_key

AUDIO_DIR = "output/audio"
RAW_AUDIO_FILE = "output/audio/raw.mp3"
CLEANED_CHUNKS_EXCEL_PATH = "output/log/cleaned_chunks.xlsx"

def compress_audio(input_file: str, output_file: str):
    """将输入音频文件压缩为低质量音频文件，用于转录"""
    if not os.path.exists(output_file):
        print(f"🗜️ Converting to low quality audio with FFmpeg ......")
        # 16000 Hz, 1 channel, (Whisper default) , 96kbps to keep more details as well as smaller file size
        subprocess.run([
            'ffmpeg', '-y', '-i', input_file, '-vn', '-b:a', '96k',
            '-ar', '16000', '-ac', '1', '-metadata', 'encoding=UTF-8',
            '-f', 'mp3', output_file
        ], check=True, stderr=subprocess.PIPE)
        print(f"🗜️ Converted <{input_file}> to <{output_file}> with FFmpeg")
    return output_file

def convert_video_to_audio(video_file: str):
    os.makedirs(AUDIO_DIR, exist_ok=True)
    if not os.path.exists(RAW_AUDIO_FILE):
        print(f"🎬➡️🎵 Converting to high quality audio with FFmpeg ......")
        subprocess.run([
            'ffmpeg', '-y', '-i', video_file, '-vn',
            '-c:a', 'libmp3lame', '-b:a', '128k',
            '-ar', '32000',
            '-ac', '1', 
            '-metadata', 'encoding=UTF-8', RAW_AUDIO_FILE
        ], check=True, stderr=subprocess.PIPE)
        print(f"🎬➡️🎵 Converted <{video_file}> to <{RAW_AUDIO_FILE}> with FFmpeg\n")

def _detect_silence(audio_file: str, start: float, end: float) -> List[float]:
    """Detect silence points in the given audio segment"""
    cmd = ['ffmpeg', '-y', '-i', audio_file, 
           '-ss', str(start), '-to', str(end),
           '-af', 'silencedetect=n=-30dB:d=0.5', 
           '-f', 'null', '-']
    
    output = subprocess.run(cmd, capture_output=True, text=True, 
                          encoding='utf-8').stderr
    
    return [float(line.split('silence_end: ')[1].split(' ')[0])
            for line in output.split('\n')
            if 'silence_end' in line]

def get_audio_duration(audio_file: str) -> float:
    """Get the duration of an audio file using ffmpeg."""
    cmd = ['ffmpeg', '-i', audio_file]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _, stderr = process.communicate()
    output = stderr.decode('utf-8', errors='ignore')
    
    try:
        duration_str = [line for line in output.split('\n') if 'Duration' in line][0]
        duration_parts = duration_str.split('Duration: ')[1].split(',')[0].split(':')
        duration = float(duration_parts[0])*3600 + float(duration_parts[1])*60 + float(duration_parts[2])
    except Exception as e:
        print(f"[red]❌ Error: Failed to get audio duration: {e}[/red]")
        duration = 0
    return duration

def split_audio(audio_file: str, target_len: int = 30*60, win: int = 60) -> List[Tuple[float, float]]:
    # 30 min 16000 Hz 96kbps ~ 22MB < 25MB required by whisper
    print("[bold blue]🔪 Starting audio segmentation...[/]")
    
    duration = get_audio_duration(audio_file)
    
    segments = []
    pos = 0
    while pos < duration:
        if duration - pos < target_len:
            segments.append((pos, duration))
            break
        win_start = pos + target_len - win
        win_end = min(win_start + 2 * win, duration)
        silences = _detect_silence(audio_file, win_start, win_end)
    
        if silences:
            target_pos = target_len - (win_start - pos)
            split_at = next((t for t in silences if t - win_start > target_pos), None)
            if split_at:
                segments.append((pos, split_at))
                pos = split_at
                continue
        segments.append((pos, pos + target_len))
        pos += target_len
    
    print(f"🔪 Audio split into {len(segments)} segments")
    return segments

def process_transcription(result: Dict) -> pd.DataFrame:
    all_words = []
    for segment in result['segments']:
        for word in segment['words']:
            # Check word length
            if len(word["word"]) > 20:
                print(f"⚠️ Warning: Detected word longer than 20 characters, skipping: {word['word']}")
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
        print(f"ℹ️ Removed {removed_rows} row(s) with empty text.")
    
    # Check for and remove words longer than 20 characters
    long_words = df[df['text'].str.len() > 20]
    if not long_words.empty:
        print(f"⚠️ Warning: Detected {len(long_words)} word(s) longer than 20 characters. These will be removed.")
        df = df[df['text'].str.len() <= 20]
    
    df['text'] = df['text'].apply(lambda x: f'"{x}"')
    df.to_excel(CLEANED_CHUNKS_EXCEL_PATH, index=False)
    print(f"📊 Excel file saved to {CLEANED_CHUNKS_EXCEL_PATH}")

def save_language(language: str):
    update_key("whisper.detected_language", language)