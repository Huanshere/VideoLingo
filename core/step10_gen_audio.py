import os, sys
import pandas as pd
from tqdm import tqdm
import soundfile as sf
import subprocess
from rich import print as rprint
from rich.panel import Panel
from rich.console import Console
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.all_tts_functions.gpt_sovits_tts import gpt_sovits_tts_for_videolingo
from core.all_tts_functions.openai_tts import openai_tts
from core.all_tts_functions.edge_tts import edge_tts
from core.all_tts_functions.azure_tts import azure_tts

console = Console()

def check_wav_duration(file_path):
    try:
        audio_info = sf.info(file_path)
        return audio_info.duration
    except Exception as e:
        raise Exception(f"Error checking duration: {str(e)}")

def parse_srt_time(time_str):
    hours, minutes, seconds = time_str.strip().split(':')
    seconds, milliseconds = seconds.split(',')
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000

def tts_main(text, save_as, number, task_df):
    from config import TTS_METHOD
    if TTS_METHOD == 'openai':
        openai_tts(text, save_as)
    elif TTS_METHOD == 'gpt_sovits':
        #! 注意 gpt_sovits_tts 只支持输出中文，输入中文或英文
        gpt_sovits_tts_for_videolingo(text, save_as, number, task_df)
    elif TTS_METHOD == 'edge_tts':
        edge_tts(text, save_as)
    elif TTS_METHOD == 'azure_tts':
        azure_tts(text, save_as)

def generate_audio(text, target_duration, save_as, number, task_df):
    from config import MIN_SPEED_FACTOR, MAX_SPEED_FACTOR
    os.makedirs('output/audio/tmp', exist_ok=True)
    temp_filename = f"output/audio/tmp/{number}_temp.wav"

    tts_main(text, temp_filename, number, task_df)

    original_duration = check_wav_duration(temp_filename)
    speed_factor = original_duration / target_duration

    # Check speed factor and adjust audio speed
    if MIN_SPEED_FACTOR <= speed_factor <= MAX_SPEED_FACTOR:
        change_audio_speed(temp_filename, save_as, speed_factor)
        final_duration = check_wav_duration(save_as)
        rprint(f"✅ {number} Adjusted audio: {save_as} | Duration: {final_duration:.2f}s | Required: {target_duration:.2f}s | Speed factor: {speed_factor:.2f}")
    elif speed_factor < MIN_SPEED_FACTOR:
        change_audio_speed(temp_filename, save_as, MIN_SPEED_FACTOR)
        final_duration = check_wav_duration(save_as)
        rprint(f"⚠️ {number} Adjusted audio: {save_as} | Duration: {final_duration:.2f}s | Required: {target_duration:.2f}s | Speed factor: {MIN_SPEED_FACTOR}")
    else:  # speed_factor > MAX_SPEED_FACTOR
        rprint(f"⚠️ {number} Speed factor out of range: {speed_factor:.2f}, attempting to simplify subtitle...")
        
        punctuation = ',.!?;:，。！？；：'
        trimmed_text = ''.join([char if char not in punctuation else ' ' for char in text]).replace('  ', ' ')
        
        rprint(f"Original subtitle: {text} | Simplified subtitle: {trimmed_text}")
        
        tts_main(trimmed_text, temp_filename, number, task_df)
        new_original_duration = check_wav_duration(temp_filename)
        new_speed_factor = new_original_duration / target_duration

        change_audio_speed(temp_filename, save_as, new_speed_factor)
        final_duration = check_wav_duration(save_as)
        rprint(f"✅ {number} Adjusted audio: {save_as} | Duration: {final_duration:.2f}s | Required: {target_duration:.2f}s | Speed factor: {new_speed_factor:.2f}")

    if os.path.exists(temp_filename):
        os.remove(temp_filename)

def change_audio_speed(input_file, output_file, speed_factor):
    atempo = speed_factor
    cmd = ['ffmpeg', '-i', input_file, '-filter:a', f'atempo={atempo}', '-y', output_file]
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            subprocess.run(cmd, check=True, stderr=subprocess.PIPE)
            return  # Success, exit the function
        except subprocess.CalledProcessError as e:
            if attempt < max_retries - 1:  # If it's not the last attempt
                rprint(f"[yellow]Warning: Failed to change audio speed, retrying in 1 second (Attempt {attempt + 1}/{max_retries})[/yellow]")
                time.sleep(1)
            else:
                rprint(f"[red]Error: Failed to change audio speed, maximum retry attempts reached ({max_retries})[/red]")
                raise e  # Re-raise the exception if all retries failed

def process_sovits_tasks():
    tasks_df = pd.read_excel("output/audio/sovits_tasks.xlsx")
    error_tasks = []
    os.makedirs('output/audio/segs', exist_ok=True)

    with console.status("[bold green]Processing tasks...") as status:
        for _, row in tqdm(tasks_df.iterrows(), total=len(tasks_df)):
            output_file = f'output/audio/segs/{row["number"]}.wav'
            if os.path.exists(output_file):
                rprint(f"[yellow]File {output_file} already exists, skipping processing[/yellow]")
                continue
            try:
                generate_audio(row['text'], float(row['duration']), output_file, row['number'], tasks_df)
            except Exception as e:
                error_tasks.append(row['number'])
                rprint(Panel(f"Error processing task {row['number']}: {str(e)}", title="Error", border_style="red"))

    if error_tasks:
        # Retry once, sometimes there might be network issues or file I/O errors
        rprint(Panel(f"The following tasks encountered errors, retrying: {', '.join(map(str, error_tasks))}", title="Retry", border_style="yellow"))
        retry_tasks = error_tasks.copy()
        error_tasks.clear()
        for task_number in retry_tasks:
            row = tasks_df[tasks_df['number'] == task_number].iloc[0]
            output_file = f'output/audio/segs/{row["number"]}.wav'
            try:
                generate_audio(row['text'], float(row['duration']), output_file, row['number'], tasks_df)
            except Exception as e:
                error_tasks.append(row['number'])
                rprint(Panel(f"Error retrying task {row['number']}: {str(e)}", title="Error", border_style="red"))

    if error_tasks:
        error_msg = f"The following tasks failed to process: {', '.join(map(str, error_tasks))}"
        rprint(Panel(error_msg, title="Failed Tasks", border_style="red"))
        raise Exception()
    
    rprint(Panel("Task processing completed", title="Success", border_style="green"))

if __name__ == "__main__":
    process_sovits_tasks()