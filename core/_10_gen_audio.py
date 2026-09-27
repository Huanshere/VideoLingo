import os
import json
from core.utils.task_literals import parse_task_literal
import time
import shutil
import subprocess
from typing import Tuple

import pandas as pd
from pydub import AudioSegment
from rich.console import Console
from rich.progress import Progress
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.utils import *
from core.utils.models import *
from core.asr_backend.audio_preprocess import get_audio_duration
from core.tts_backend.tts_main import tts_main

console = Console()

TEMP_FILE_TEMPLATE = f"{_AUDIO_TMP_DIR}/{{}}_temp.wav"
OUTPUT_FILE_TEMPLATE = f"{_AUDIO_SEGS_DIR}/{{}}.wav"
TRUNCATED_LOG = "output/log/dub_truncated.json"
WARMUP_SIZE = 5

def parse_df_srt_time(time_str: str) -> float:
    """Convert SRT time format to seconds"""
    hours, minutes, seconds = time_str.strip().split(':')
    seconds, milliseconds = seconds.split('.')
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000

def adjust_audio_speed(input_file: str, output_file: str, speed_factor: float) -> None:
    """Adjust audio speed and handle edge cases"""
    # If the speed factor is close to 1, directly copy the file
    if abs(speed_factor - 1.0) < 0.001:
        shutil.copy2(input_file, output_file)
        return
        
    atempo = speed_factor
    cmd = ['ffmpeg', '-i', input_file, '-filter:a', f'atempo={atempo}', '-y', output_file]
    input_duration = get_audio_duration(input_file)
    max_retries = 2
    for attempt in range(max_retries):
        try:
            subprocess.run(cmd, check=True, stderr=subprocess.PIPE)
            output_duration = get_audio_duration(output_file)
            expected_duration = input_duration / speed_factor
            diff = output_duration - expected_duration
            # If the output duration exceeds the expected duration, but the input audio is less than 3 seconds, and the error is within 0.1 seconds, truncate to the expected length
            if output_duration >= expected_duration * 1.02 and input_duration < 3 and diff <= 0.1:
                audio = AudioSegment.from_wav(output_file)
                trimmed_audio = audio[:(expected_duration * 1000)]  # pydub uses milliseconds
                trimmed_audio.export(output_file, format="wav")
                print(f"✂️ Trimmed to expected duration: {expected_duration:.2f} seconds")
                return
            elif output_duration >= expected_duration * 1.02:
                # Keep going with the expected length instead of failing the whole dubbing
                truncate_audio(output_file, expected_duration)
                rprint(f"[yellow]⚠️ Audio duration abnormal, trimmed {output_file} from {output_duration:.2f}s to {expected_duration:.2f}s (speed factor={speed_factor})[/yellow]")
            return
        except subprocess.CalledProcessError as e:
            if attempt < max_retries - 1:
                rprint(f"[yellow]⚠️ Audio speed adjustment failed, retrying in 1s ({attempt + 1}/{max_retries})[/yellow]")
                time.sleep(1)
            else:
                rprint(f"[red]❌ Audio speed adjustment failed, max retries reached ({max_retries})[/red]")
                raise e

def truncate_audio(audio_file: str, keep_seconds: float) -> None:
    """Cut a wav file to keep_seconds, with a short fade so the cut does not click"""
    audio = AudioSegment.from_wav(audio_file)
    keep_ms = int(max(0, keep_seconds) * 1000)
    if keep_ms < 10:  # nothing left to hear; an empty file would break the merge step
        audio = AudioSegment.silent(duration=10, frame_rate=audio.frame_rate)
    else:
        audio = audio[:keep_ms].fade_out(min(50, keep_ms))
    audio.export(audio_file, format="wav")

def process_row(row: pd.Series, tasks_df: pd.DataFrame) -> Tuple[int, float]:
    """Helper function for processing single row data"""
    number = row['number']
    lines = parse_task_literal(row['lines'])
    real_dur = 0
    for line_index, line in enumerate(lines):
        temp_file = TEMP_FILE_TEMPLATE.format(f"{number}_{line_index}")
        tts_main(line, temp_file, number, tasks_df)
        real_dur += get_audio_duration(temp_file)
    return number, real_dur

def generate_tts_audio(tasks_df: pd.DataFrame) -> pd.DataFrame:
    """Generate TTS audio sequentially and calculate actual duration"""
    # pandas 3 rejects fractional durations assigned into an integer column.
    tasks_df['real_dur'] = 0.0
    rprint("[bold green]🎯 Starting TTS audio generation...[/bold green]")
    
    with Progress() as progress:
        task = progress.add_task("[cyan]🔄 Generating TTS audio...", total=len(tasks_df))
        
        # warm up for first 5 rows
        warmup_size = min(WARMUP_SIZE, len(tasks_df))
        for _, row in tasks_df.head(warmup_size).iterrows():
            try:
                check_cancel()
                number, real_dur = process_row(row, tasks_df)
                tasks_df.loc[tasks_df['number'] == number, 'real_dur'] = real_dur
                progress.advance(task)
            except Exception as e:
                rprint(f"[red]❌ Error in warmup: {str(e)}[/red]")
                raise e
        
        # for gpt_sovits, do not use parallel to avoid mistakes
        max_workers = load_key("max_workers") if load_key("tts_method") != "gpt_sovits" else 1
        # parallel processing for remaining tasks
        if len(tasks_df) > warmup_size:
            remaining_tasks = tasks_df.iloc[warmup_size:].copy()
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(process_row, row, tasks_df.copy())
                    for _, row in remaining_tasks.iterrows()
                ]
                
                try:
                    for future in as_completed(futures):
                        check_cancel()
                        try:
                            number, real_dur = future.result()
                            tasks_df.loc[tasks_df['number'] == number, 'real_dur'] = real_dur
                            progress.advance(task)
                        except Exception as e:
                            rprint(f"[red]❌ Error: {str(e)}[/red]")
                            raise e
                except BaseException:
                    for f in futures:
                        f.cancel()
                    raise

    rprint("[bold green]✨ TTS audio generation completed![/bold green]")
    return tasks_df

def process_chunk(chunk_df: pd.DataFrame, accept: float, min_speed: float, max_speed: float = None) -> tuple[float, bool]:
    """Process audio chunk and calculate speed factor"""
    chunk_durs = chunk_df['real_dur'].sum()
    tol_durs = chunk_df['tol_dur'].sum()
    durations = tol_durs - chunk_df.iloc[-1]['tolerance']
    all_gaps = chunk_df['gap'].sum() - chunk_df.iloc[-1]['gap']
    
    keep_gaps = True
    speed_var_error = 0.1

    def speed_for(audio_dur, available):
        # No usable room (a subtitle of a few milliseconds) counts as "as fast as allowed"
        room = available - speed_var_error
        return audio_dur / room if room > 0 else float('inf')

    if (chunk_durs + all_gaps) / accept < durations:
        speed_factor = max(min_speed, speed_for(chunk_durs + all_gaps, durations))
    elif chunk_durs / accept < durations:
        speed_factor = max(min_speed, speed_for(chunk_durs, durations))
        keep_gaps = False
    elif (chunk_durs + all_gaps) / accept < tol_durs:
        speed_factor = max(min_speed, speed_for(chunk_durs + all_gaps, tol_durs))
    else:
        speed_factor = speed_for(chunk_durs, tol_durs)
        keep_gaps = False

    # Faster than this is not intelligible; what does not fit is truncated in merge_chunks
    if max_speed is not None:
        speed_factor = min(speed_factor, max(max_speed, min_speed))
        
    return round(speed_factor, 3), keep_gaps

def merge_chunks(tasks_df: pd.DataFrame) -> pd.DataFrame:
    """Merge audio chunks and adjust timeline"""
    rprint("[bold blue]🔄 Starting audio chunks processing...[/bold blue]")
    accept = load_key("speed_factor.accept")
    min_speed = load_key("speed_factor.min")
    max_speed = load_key("speed_factor.max")
    chunk_start = 0
    truncated = []
    
    tasks_df['new_sub_times'] = None
    
    for index, row in tasks_df.iterrows():
        if row['cut_off'] == 1:
            check_cancel()
            chunk_df = tasks_df.iloc[chunk_start:index+1].reset_index(drop=True)
            speed_factor, keep_gaps = process_chunk(chunk_df, accept, min_speed, max_speed)
            placed = []  # (main DataFrame index, line index, audio file, text) in timeline order
            
            # 🎯 Step1: Start processing new timeline
            chunk_start_time = parse_df_srt_time(chunk_df.iloc[0]['start_time'])
            chunk_end_time = parse_df_srt_time(chunk_df.iloc[-1]['end_time']) + chunk_df.iloc[-1]['tolerance'] # 加上tolerance才是这一块的结束
            cur_time = chunk_start_time
            for i, row in chunk_df.iterrows():
                # If i is not 0, which is not the first row of the chunk, cur_time needs to be added with the gap of the previous row, remember to divide by speed_factor
                if i != 0 and keep_gaps:
                    cur_time += chunk_df.iloc[i-1]['gap']/speed_factor
                new_sub_times = []
                number = row['number']
                lines = parse_task_literal(row['lines'])
                for line_index, line in enumerate(lines):
                    # 🔄 Step2: Start speed change and save as OUTPUT_FILE_TEMPLATE
                    temp_file = TEMP_FILE_TEMPLATE.format(f"{number}_{line_index}")
                    output_file = OUTPUT_FILE_TEMPLATE.format(f"{number}_{line_index}")
                    adjust_audio_speed(temp_file, output_file, speed_factor)
                    ad_dur = get_audio_duration(output_file)
                    new_sub_times.append([float(cur_time), float(cur_time+ad_dur)])
                    cur_time += ad_dur
                # 🔄 Step3: Find corresponding main DataFrame index and update new_sub_times
                main_df_idx = tasks_df[tasks_df['number'] == row['number']].index[0]
                tasks_df.at[main_df_idx, 'new_sub_times'] = new_sub_times
                placed += [(main_df_idx, line_index, OUTPUT_FILE_TEMPLATE.format(f"{number}_{line_index}"), line)
                           for line_index, line in enumerate(lines)]
                # 🎯 Step4: Choose emoji based on speed_factor and accept comparison
                emoji = "⚡" if speed_factor <= accept else "⚠️"
                rprint(f"[cyan]{emoji} Processed chunk {chunk_start} to {index} with speed factor {speed_factor}[/cyan]")
            # 🔄 Step5: What still exceeds the chunk at the highest speed is truncated, from the end
            if cur_time > chunk_end_time:
                rprint(f"[yellow]⚠️ Chunk {chunk_start} to {index} exceeds by {cur_time - chunk_end_time:.3f}s at speed factor {speed_factor}, truncating[/yellow]")
                for main_df_idx, line_index, audio_file, line in reversed(placed):
                    times = tasks_df.at[main_df_idx, 'new_sub_times']
                    start, end = times[line_index]
                    if end <= chunk_end_time:
                        break
                    # NumPy 2 scalar repr includes np.float64(...), which is
                    # not a portable literal when Excel serializes this list.
                    new_start = float(min(start, chunk_end_time))
                    truncate_audio(audio_file, chunk_end_time - new_start)
                    times[line_index] = [new_start, float(chunk_end_time)]
                    tasks_df.at[main_df_idx, 'new_sub_times'] = times
                    truncated.append({
                        "number": int(tasks_df.at[main_df_idx, 'number']), "line": str(line),
                        "spoken_seconds": round(float(end - start), 3),
                        "kept_seconds": round(float(chunk_end_time - new_start), 3),
                        "speed_factor": float(speed_factor),
                    })
            chunk_start = index+1
    
    save_truncated_log(truncated)
    rprint("[bold green]✅ Audio chunks processing completed![/bold green]")
    return tasks_df

def save_truncated_log(truncated: list) -> None:
    """List the lines whose dubbing was cut so they can be shortened by hand"""
    if os.path.exists(TRUNCATED_LOG):
        os.remove(TRUNCATED_LOG)
    if not truncated:
        return
    truncated = sorted(reversed(truncated), key=lambda item: item["number"])  # chunks were walked backwards
    os.makedirs(os.path.dirname(TRUNCATED_LOG), exist_ok=True)
    with open(TRUNCATED_LOG, 'w', encoding='utf-8') as f:
        json.dump(truncated, f, ensure_ascii=False, indent=4)
    rprint(f"[yellow]⚠️ {len(truncated)} dubbed line(s) did not fit their time slot and were truncated, see `{TRUNCATED_LOG}`:[/yellow]")
    for item in truncated:
        rprint(f"[yellow]   #{item['number']} kept {item['kept_seconds']}s of {item['spoken_seconds']}s: {item['line']}[/yellow]")

def gen_audio() -> None:
    """Main function: Generate audio and process timeline"""
    rprint("[bold magenta]🚀 Starting audio generation process...[/bold magenta]")
    
    # 🎯 Step1: Create necessary directories
    os.makedirs(_AUDIO_TMP_DIR, exist_ok=True)
    os.makedirs(_AUDIO_SEGS_DIR, exist_ok=True)
    
    # 📝 Step2: Load task file
    tasks_df = pd.read_excel(_8_1_AUDIO_TASK)
    rprint("[green]📊 Loaded task file successfully[/green]")
    
    # 🔊 Step3: Generate TTS audio
    tasks_df = generate_tts_audio(tasks_df)
    
    # 🔄 Step4: Merge audio chunks
    tasks_df = merge_chunks(tasks_df)
    
    # 💾 Step5: Save results
    tasks_df.to_excel(_8_1_AUDIO_TASK, index=False)
    rprint("[bold green]🎉 Audio generation completed successfully![/bold green]")

if __name__ == "__main__":
    gen_audio()
