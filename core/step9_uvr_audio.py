import re
import subprocess
from pydub import AudioSegment
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from third_party.uvr5.uvr5_for_videolingo import uvr5_for_videolingo
from rich import print as rprint
from rich.panel import Panel
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
import pandas as pd

console = Console()

def parse_srt(srt_content):
    pattern = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n((?:.+\n)+)')
    matches = pattern.findall(srt_content)
    return [{'index': int(m[0]), 'start': m[1], 'end': m[2], 'text': m[3].strip()} for m in matches]  # 解析SRT内容

def time_to_ms(time_str):
    h, m, s = time_str.split(':')
    s, ms = s.split(',')
    return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)  # 将时间字符串转换为毫秒

def extract_audio(input_video, start_time, end_time, output_file):
    start_ms = time_to_ms(start_time)
    end_ms = time_to_ms(end_time)
    
    temp_audio = 'temp_audio.wav'
    with console.status("[bold green]Extracting audio..."):
        subprocess.run(['ffmpeg', '-y', '-i', input_video, '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2', temp_audio], check=True)
    
    audio = AudioSegment.from_wav(temp_audio)
    extract = audio[start_ms:end_ms]
    extract.export(output_file, format="wav")
    
    os.remove(temp_audio)

def uvr_audio_main(input_video):
    output_dir = 'output/audio'
    if os.path.exists(os.path.join(output_dir, 'background.wav')):
        rprint(Panel(f"{os.path.join(output_dir, 'background.wav')} already exists, skip.", title="Info", border_style="blue"))
        return

    # step1 uvr5 降噪完整音频
    full_audio_path = os.path.join(output_dir, 'full_audio.wav')
    
    subprocess.run(['ffmpeg', '-y', '-i', input_video, '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2', full_audio_path], check=True)
    with console.status("[bold green]UVR5 processing full audio, Might take a while to save audio after 100% ..."):
        uvr5_for_videolingo(full_audio_path, output_dir)
    
    os.remove(full_audio_path)
    original_vocal_path = os.path.join(output_dir, 'original_vocal.wav')
    background_path = os.path.join(output_dir, 'background.wav')
    
    if os.path.exists(original_vocal_path):
        os.remove(original_vocal_path)
    if os.path.exists(background_path):
        os.remove(background_path)
    
    os.rename(os.path.join(output_dir, 'vocal_full_audio.wav_10.wav'), original_vocal_path)
    os.rename(os.path.join(output_dir, 'instrument_full_audio.wav_10.wav'), background_path)
    
    rprint(Panel("Full audio extracted, cleaned and saved as original_vocal.wav and background.wav", title="Success", border_style="green"))

    # step2 提取音频
    df = pd.read_excel(os.path.join(output_dir, 'sovits_tasks.xlsx'))
    
    refers_dir = os.path.join(output_dir, 'refers')
    os.makedirs(refers_dir, exist_ok=True)
    
    original_vocal_path = os.path.join(output_dir, 'original_vocal.wav')
    
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    )
    
    with progress:
        extract_task = progress.add_task("[cyan]Extracting audio segments...", total=len(df))
        
        for _, row in df.iterrows():
            number = row['number']
            start_time = row['start_time']
            end_time = row['end_time']
            output_file = os.path.join(refers_dir, f"{number}.wav")
            
            ffmpeg_command = [
                'ffmpeg',
                '-y',
                '-i', original_vocal_path,
                '-ss', start_time,
                '-to', end_time,
                '-c', 'copy',
                '-loglevel', 'error',  # 添加这一行来抑制输出
                output_file
            ]
            
            subprocess.run(ffmpeg_command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            progress.update(extract_task, advance=1)
    rprint(Panel(f"Audio segments extracted and saved in {refers_dir}", title="Success", border_style="green"))
    
if __name__ == "__main__":
    from core.step1_ytdlp import find_video_files
    input_video = find_video_files()
    uvr_audio_main(input_video)