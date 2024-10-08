import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config_utils import load_key
from datetime import datetime
import pandas as pd
import subprocess
from pydub import AudioSegment
from rich import print as rprint
import numpy as np
import soundfile as sf
import cv2

def time_to_datetime(time_str):
    return datetime.strptime(time_str, '%H:%M:%S.%f')

def create_silence(duration, output_file):
    sample_rate = 32000
    num_samples = int(duration * sample_rate)
    silence = np.zeros(num_samples, dtype=np.float32)
    sf.write(output_file, silence, sample_rate)

def merge_all_audio():
    # Define input and output paths
    input_excel = 'output/audio/sovits_tasks.xlsx'
    output_audio = 'output/trans_vocal_total.wav'
        
    df = pd.read_excel(input_excel)
    
    # Get the sample rate of the first audio file
    first_audio = f'output/audio/segs/{df.iloc[0]["number"]}.wav'
    sample_rate = AudioSegment.from_wav(first_audio).frame_rate

    # Create an empty AudioSegment object
    merged_audio = AudioSegment.silent(duration=0, frame_rate=sample_rate)

    prev_target_start_time = None
    prev_actual_duration = 0
    
    for index, row in df.iterrows():
        number = row['number']
        start_time = row['start_time']
        input_audio = f'output/audio/segs/{number}.wav'
        
        if not os.path.exists(input_audio):
            rprint(f"[bold yellow]Warning: File {input_audio} does not exist, skipping this file.[/bold yellow]")
            continue
        
        audio_segment = AudioSegment.from_wav(input_audio)
        actual_duration = len(audio_segment) / 1000  # Convert to seconds
        target_start_time = time_to_datetime(start_time)
        
        silence_duration = (target_start_time - datetime(1900, 1, 1)).total_seconds() if prev_target_start_time is None else (target_start_time - prev_target_start_time).total_seconds() - prev_actual_duration
        
        if silence_duration > 0:
            silence = AudioSegment.silent(duration=int(silence_duration * 1000), frame_rate=sample_rate)
            merged_audio += silence
        
        merged_audio += audio_segment
        
        prev_target_start_time = target_start_time
        prev_actual_duration = actual_duration

    # Export the merged audio
    merged_audio.export(output_audio, format="wav")
    rprint(f"[bold green]Audio file successfully merged, output file: {output_audio}[/bold green]")

def merge_video_audio():
    """Merge video and audio, and reduce video volume"""
    video_file = "output/output_video_with_subs.mp4"
    background_file = 'output/audio/background.wav'
    original_vocal = 'output/audio/original_vocal.wav'
    audio_file = "output/trans_vocal_total.wav"    
    output_file = "output/output_video_with_audio.mp4"

    if os.path.exists(output_file):
        rprint(f"[bold yellow]{output_file} already exists, skipping processing.[/bold yellow]")
        return
    
    if load_key("resolution") == '0x0':
        rprint("[bold yellow]Warning: A 0-second black video will be generated as a placeholder as Resolution is set to 0x0.[/bold yellow]")

        # Create a black frame
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_file, fourcc, 1, (1920, 1080))
        out.write(frame)
        out.release()

        rprint("[bold green]Placeholder video has been generated.[/bold green]")
        return

    # Merge video and audio
    original_volume = load_key("original_volume")
    dub_volume = load_key("dub_volume")
    cmd = ['ffmpeg', '-y', '-i', video_file, '-i', background_file, '-i', original_vocal, '-i', audio_file, '-filter_complex', f'[1:a]volume=1[a1];[2:a]volume={original_volume}[a2];[3:a]volume={dub_volume}[a3];[a1][a2][a3]amix=inputs=3:duration=first:dropout_transition=3[a]', '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', output_file]

    try:
        subprocess.run(cmd, check=True)
        rprint(f"[bold green]Video and audio successfully merged into {output_file}[/bold green]")
    except subprocess.CalledProcessError as e:
        rprint(f"[bold red]Error merging video and audio: {e}[/bold red]")
    
    # Delete temporary audio file
    if os.path.exists('tmp_audio.wav'):
        os.remove('tmp_audio.wav')

def merge_main():
    merge_all_audio()
    merge_video_audio()
    
if __name__ == "__main__":
    merge_main()