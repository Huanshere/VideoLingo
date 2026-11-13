import os
from rich.panel import Panel
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from core.utils import *
from core.utils.models import *
import pandas as pd
import soundfile as sf
console = Console()
from core.utils.models import *

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


def _reference_source_audio():
    """Return the configured source track for voice-cloning references."""
    if not load_key("demucs"):
        return _RAW_AUDIO_FILE

    # Vocal separation stays optional: without it the reference keeps the original
    # background track, which is the upstream fallback behaviour.
    from importlib.util import find_spec

    if find_spec("demucs") is None:
        rprint(Panel(
            "Vocal separation is unavailable; using the original audio for references. "
            "The dubbed video will not keep the original background sound.",
            title="Info", border_style="yellow",
        ))
        return _RAW_AUDIO_FILE

    from core.asr_backend.demucs_vl import demucs_audio

    demucs_audio()
    source = _VOCAL_AUDIO_FILE
    if not os.path.exists(source):
        raise FileNotFoundError(f"Reference source audio was not created: {source}")
    return source

def extract_refer_audio_main():
    # Create output directory
    os.makedirs(_AUDIO_REFERS_DIR, exist_ok=True)

    # Read the task list first so interrupted runs only skip when every
    # reference clip required by the current workbook is already present.
    df = pd.read_excel(_8_1_AUDIO_TASK)
    expected_references = [
        os.path.join(_AUDIO_REFERS_DIR, f"{number}.wav")
        for number in df['number'].tolist()
    ]
    if expected_references and all(os.path.exists(path) for path in expected_references):
        rprint(Panel("Reference audio already exists, skipping extraction", title="Info", border_style="blue"))
        return

    # Use the raw track when vocal separation is disabled; Demucs stays optional.
    data, sr = sf.read(_reference_source_audio())
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    ) as progress:
        task = progress.add_task("Extracting audio segments...", total=len(df))
        
        for _, row in df.iterrows():
            out_file = os.path.join(_AUDIO_REFERS_DIR, f"{row['number']}.wav")
            extract_audio(data, sr, row['start_time'], row['end_time'], out_file)
            progress.update(task, advance=1)
            
    rprint(Panel(f"Audio segments saved to {_AUDIO_REFERS_DIR}", title="Success", border_style="green"))

if __name__ == "__main__":
    extract_refer_audio_main()
