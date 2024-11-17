import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rich import print as rprint
from rich.panel import Panel
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
import pandas as pd
import soundfile as sf
console = Console()
from core.all_whisper_methods.demucs_vl import demucs_main, VOCAL_AUDIO_FILE

# Simplified path definitions
REF_DIR = 'output/audio/refers'
SEG_DIR = 'output/audio/segs'
TASKS_FILE = 'output/audio/tts_tasks.xlsx'

def time_to_samples(time_str, sr):
    """Unified time conversion function"""
    h, m, s = time_str.split(':')
    s, ms = s.split(',') if ',' in s else (s, '0')
    seconds = int(h) * 3600 + int(m) * 60 + float(s) + float(ms) / 1000
    return int(seconds * sr)

def extract_audio(audio_data, sr, start_time, end_time, out_file):
    """Simplified audio extraction function"""
    start = time_to_samples(start_time, sr)
    end = time_to_samples(end_time, sr)
    sf.write(out_file, audio_data[start:end], sr)

def extract_refer_audio_main():
    demucs_main() #!!! in case demucs is not run
    if os.path.exists(os.path.join(SEG_DIR, '1.wav')):
        rprint(Panel("Audio segments already exist, skipping extraction", title="Info", border_style="blue"))
        return

    # Create output directory
    os.makedirs(REF_DIR, exist_ok=True)
    
    # Read task file and audio data
    df = pd.read_excel(TASKS_FILE)
    data, sr = sf.read(VOCAL_AUDIO_FILE)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    ) as progress:
        task = progress.add_task("Extracting audio segments...", total=len(df))
        
        for _, row in df.iterrows():
            out_file = os.path.join(REF_DIR, f"{row['number']}.wav")
            extract_audio(data, sr, row['start_time'], row['end_time'], out_file)
            progress.update(task, advance=1)
            
    rprint(Panel(f"Audio segments saved to {REF_DIR}", title="Success", border_style="green"))

if __name__ == "__main__":
    extract_refer_audio_main()