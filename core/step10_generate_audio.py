import os
import pandas as pd
from tqdm import tqdm
import soundfile as sf
import sys
from pathlib import Path
import requests
import json
import subprocess
from rich import print as rprint
from rich.panel import Panel
from rich.console import Console
from rich.table import Table
import matplotlib.pyplot as plt

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.prompts_storage import get_subtitle_trim_prompt
from core.ask_gpt import ask_gpt

console = Console()
speed_factors = []

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

def generate_audio(text, target_duration, save_as, number):
    from config import step9_trim_model, MIN_SPEED_FACTOR, MAX_SPEED_FACTOR
    temp_filename = f"output/audio/tmp/{number}_temp.wav"

    tts_function(text, "zh", 1.0, temp_filename)
    original_duration = check_wav_duration(temp_filename)

    speed_factor = original_duration / target_duration

    if MIN_SPEED_FACTOR <= speed_factor <= MAX_SPEED_FACTOR:
        change_audio_speed(temp_filename, save_as, speed_factor)
        final_duration = check_wav_duration(save_as)
        rprint(Panel(f"✅ {number} 调整后的音频: {save_as}\n时长: {final_duration:.2f}秒\n要求的时长: {target_duration:.2f}秒\n速度因子: {speed_factor:.2f}", title="音频调整成功", border_style="green"))
        speed_factors.append(speed_factor)
    elif speed_factor < MIN_SPEED_FACTOR:
        change_audio_speed(temp_filename, save_as, MIN_SPEED_FACTOR)
        final_duration = check_wav_duration(save_as)
        rprint(Panel(f"⚠️ {number} 调整后的音频: {save_as}\n时长: {final_duration:.2f}秒\n要求的时长: {target_duration:.2f}秒\n速度因子: {MIN_SPEED_FACTOR}", title="音频调整成功（最小速度）", border_style="yellow"))
        speed_factors.append(MIN_SPEED_FACTOR)
    else:  # speed_factor > MAX_SPEED_FACTOR
        rprint(Panel(f"⚠️ {number} 速度因子超出范围: {speed_factor:.2f}, 正在尝试精简字幕...", title="速度因子超出范围", border_style="red"))
        prompt = get_subtitle_trim_prompt(text, target_duration, fierce_mode=True)
        response = ask_gpt(prompt, model=step9_trim_model, response_json=True, log_title='sovits_trim')
        trimmed_text = response['trans_text_processed']
        
        table = Table(title="字幕精简结果")
        table.add_column("原字幕", style="cyan")
        table.add_column("精简后字幕", style="green")
        table.add_row(text, trimmed_text)
        console.print(table)
        
        generate_audio(trimmed_text, target_duration, save_as, number)  # 递归调用
        return

    if os.path.exists(temp_filename):
        os.remove(temp_filename)

def change_audio_speed(input_file, output_file, speed_factor):
    atempo = speed_factor
    cmd = [
        'ffmpeg',
        '-i', input_file,
        '-filter:a', f'atempo={atempo}',
        '-y',
        output_file
    ]
    
    try:
        subprocess.run(cmd, check=True, stderr=subprocess.PIPE)
        rprint(f"[bold green]音频速度调整成功:[/bold green] {output_file}")
    except subprocess.CalledProcessError as e:
        rprint(f"[bold red]音频速度调整失败:[/bold red] {e.stderr.decode()}")

def tts_function(text, text_lang, speed_factor=1.0, save_path=None):
    from config import DUBBING_CHARACTER
    current_dir = Path.cwd()
    model_path = current_dir / "_model_cache" / "GPT_SoVITS" / "trained" / DUBBING_CHARACTER
    config_path = model_path / "infer_config.json"
    config = json.loads(config_path.read_text(encoding='utf-8'))
    
    default_emotion = config['emotion_list']['default']
    ref_audio_path = model_path / default_emotion['ref_wav_path']
    
    payload = {
        'text': text,
        'text_lang': text_lang,
        'ref_audio_path': str(ref_audio_path),
        'prompt_lang': default_emotion['prompt_language'],
        'prompt_text': default_emotion['prompt_text'],
        "speed_factor": speed_factor,
    }

    response = requests.post('http://127.0.0.1:9880/tts', json=payload)
    if response.status_code == 200:
        if save_path:
            full_save_path = current_dir / save_path
            full_save_path.parent.mkdir(parents=True, exist_ok=True)
            full_save_path.write_bytes(response.content)
            rprint(f"[bold green]音频保存成功:[/bold green] {full_save_path}")
        return response.content
    else:
        rprint(f"[bold red]TTS请求失败，状态码:[/bold red] {response.status_code}")
        return None

def process_sovits_tasks():
    tasks_df = pd.read_excel("output/audio/sovits_tasks.xlsx")
    error_tasks = []
    with console.status("[bold green]处理任务中...") as status:
        for _, row in tqdm(tasks_df.iterrows(), total=len(tasks_df)):
            number = row['number']
            duration = float(row['duration'])
            text = row['text']
            output_file = f'output/audio/segs/{number}.wav'

            os.makedirs('output/audio/segs', exist_ok=True)

            if os.path.exists(output_file):
                rprint(f"[yellow]文件 {output_file} 已存在,跳过处理[/yellow]")
                continue
            
            try:
                generate_audio(text, duration, output_file, number)
            except Exception as e:
                error_tasks.append(number)
                rprint(Panel(f"任务 {number} 处理出错: {str(e)}", title="错误", border_style="red"))

    if error_tasks:
        error_msg = f"以下任务处理出错: {', '.join(map(str, error_tasks))}，请检查 output/audio/sovits_tasks.xlsx 中的对应内容并修改。"
        rprint(Panel(error_msg, title="处理失败的任务", border_style="red"))
        raise Exception(error_msg)
    
    rprint(Panel("任务处理完成", title="成功", border_style="green"))

    # 绘制速度因子直方图
    plt.figure(figsize=(10, 6))
    plt.hist(speed_factors, bins=20, edgecolor='black')
    plt.title('Speed Factor Distribution')
    plt.xlabel('Speed Factor')
    plt.ylabel('Frequency')
    plt.savefig('output/speed_factor_histogram.png')
    plt.close()
    rprint(Panel("速度因子直方图已保存至 output/speed_factor_histogram.png", title="统计信息", border_style="blue"))

if __name__ == "__main__":
    process_sovits_tasks()