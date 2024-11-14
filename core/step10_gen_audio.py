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
from core.all_tts_functions.fish_tts import fish_tts
from core.all_tts_functions.azure_tts import azure_tts
from core.prompts_storage import get_subtitle_trim_prompt
from core.ask_gpt import ask_gpt
from core.config_utils import load_key

console = Console()

TEMP_DIR = 'output/audio/tmp'
SEGS_DIR = 'output/audio/segs'
TASKS_FILE = "output/audio/sovits_tasks.xlsx"
TEMP_FILE_TEMPLATE = f"{TEMP_DIR}/{{}}_temp.wav"
OUTPUT_FILE_TEMPLATE = f"{SEGS_DIR}/{{}}.wav"

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
    TTS_METHOD = load_key("tts_method")
    if TTS_METHOD == 'openai_tts':
        openai_tts(text, save_as)
    elif TTS_METHOD == 'gpt_sovits':
        #! 注意 gpt_sovits_tts 只支持输出中文，输入中文或英文
        gpt_sovits_tts_for_videolingo(text, save_as, number, task_df)
    elif TTS_METHOD == 'fish_tts':
        fish_tts(text, save_as)
    elif TTS_METHOD == 'azure_tts':
        azure_tts(text, save_as)

def generate_audio(text, target_duration, save_as, number, task_df):
    MIN_SPEED = load_key("speed_factor.min")
    MAX_SPEED = load_key("speed_factor.max")
    os.makedirs(TEMP_DIR, exist_ok=True)
    temp_file = TEMP_FILE_TEMPLATE.format(number)

    # handle empty text or nan
    if pd.isna(text) or not str(text).strip():
        # generate silent audio
        cmd = ['ffmpeg', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=mono', '-t', '0.1', '-q:a', '0', '-y', save_as]
        subprocess.run(cmd, check=True, stderr=subprocess.PIPE)
        rprint(f"ℹ️  {number} Generated silent audio for empty text: {save_as}")
        return

    tts_main(text, temp_file, number, task_df)

    original_duration = check_wav_duration(temp_file)
    # -0.03 to avoid the duration is too close to the target_duration
    speed_factor = original_duration / (target_duration-0.03)

    # Check speed factor and adjust audio speed
    if MIN_SPEED <= speed_factor <= MAX_SPEED:
        change_audio_speed(temp_file, save_as, speed_factor)
        final_duration = check_wav_duration(save_as)
        rprint(f"✅ {number} Adjusted audio: {save_as} | Duration: {final_duration:.2f}s | Required: {target_duration:.2f}s | Speed factor: {speed_factor:.2f}")
    elif speed_factor < MIN_SPEED:
        change_audio_speed(temp_file, save_as, MIN_SPEED)
        final_duration = check_wav_duration(save_as)
        rprint(f"⚠️ {number} Adjusted audio: {save_as} | Duration: {final_duration:.2f}s | Required: {target_duration:.2f}s | Speed factor: {MIN_SPEED}")
    else:  # speed_factor > MAX_SPEED
        rprint(f"🚨 {number} Speed factor out of range: {speed_factor:.2f}, attempting to simplify subtitle...")
        
        original_text = text
        prompt = get_subtitle_trim_prompt(text, target_duration)
        response = ask_gpt(prompt, response_json=True, log_title='subtitle_trim')
        shortened_text = response['result']

        rprint(f"Original subtitle: {original_text} | Simplified subtitle: {shortened_text}")
        
        tts_main(shortened_text, temp_file, number, task_df)
        new_original_duration = check_wav_duration(temp_file)
        new_speed_factor = new_original_duration / (target_duration-0.03)

        if MIN_SPEED <= new_speed_factor <= MAX_SPEED:
            change_audio_speed(temp_file, save_as, new_speed_factor)
            final_duration = check_wav_duration(save_as)
            rprint(f"✅ {number} Adjusted audio: {save_as} | Duration: {final_duration:.2f}s | Required: {target_duration:.2f}s | Speed factor: {new_speed_factor:.2f}")
        elif new_speed_factor > MAX_SPEED:
            rprint(f"🚔 {number} Speed factor still out of range after simplification: {new_speed_factor:.2f}")
            change_audio_speed(temp_file, save_as, new_speed_factor) #! force adjust
            final_duration = check_wav_duration(save_as)
            rprint(f"🚔 {number} Forced adjustment: {save_as} | Duration: {final_duration:.2f}s | Required: {target_duration:.2f}s | Speed factor: {new_speed_factor}")
        elif new_speed_factor < MIN_SPEED:
            rprint(f"⚠️ {number} Speed factor too low after simplification: {new_speed_factor:.2f}")
            change_audio_speed(temp_file, save_as, MIN_SPEED)
            final_duration = check_wav_duration(save_as)
            rprint(f"⚠️ {number} Forced adjustment: {save_as} | Duration: {final_duration:.2f}s | Required: {target_duration:.2f}s | Speed factor: {MIN_SPEED}")
    
    #! check duration for safety
    if final_duration > target_duration:
        rprint(f"❎ {number} Final duration is longer than target duration: {final_duration:.2f}s | Required: {target_duration:.2f}s. This is a bug, please report it.")
        raise Exception()
    
    if os.path.exists(temp_file):
        os.remove(temp_file)

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
    tasks_df = pd.read_excel(TASKS_FILE)
    errors = []
    os.makedirs(SEGS_DIR, exist_ok=True)

    with console.status("[bold green]Processing tasks...") as status:
        for _, row in tqdm(tasks_df.iterrows(), total=len(tasks_df)):
            out_file = OUTPUT_FILE_TEMPLATE.format(row["number"])
            if os.path.exists(out_file):
                rprint(f"[yellow]File {out_file} already exists, skipping[/yellow]")
                continue
            try:
                generate_audio(row['text'], float(row['duration']), out_file, row['number'], tasks_df)
            except Exception as e:
                errors.append(row['number'])
                rprint(Panel(f"Error processing task {row['number']}: {str(e)}", title="Error", border_style="red"))

    if errors:
        # Retry once, sometimes there might be network issues or file I/O errors
        rprint(Panel(f"The following tasks encountered errors, retrying: {', '.join(map(str, errors))}", title="Retry", border_style="yellow"))
        retry_tasks = errors.copy()
        errors.clear()
        for task_number in retry_tasks:
            row = tasks_df[tasks_df['number'] == task_number].iloc[0]
            out_file = OUTPUT_FILE_TEMPLATE.format(row["number"])
            try:
                generate_audio(row['text'], float(row['duration']), out_file, row['number'], tasks_df)
            except Exception as e:
                errors.append(row['number'])
                rprint(Panel(f"Error retrying task {row['number']}: {str(e)}", title="Error", border_style="red"))

    if errors:
        error_msg = f"The following tasks failed to process: {', '.join(map(str, errors))}"
        rprint(Panel(error_msg, title="Failed Tasks", border_style="red"))
        raise Exception("tasks failed to process, please check cli output for details")
    
    rprint(Panel("Task processing completed", title="Success", border_style="green"))

if __name__ == "__main__":
    process_sovits_tasks()