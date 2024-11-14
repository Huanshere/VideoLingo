import os, sys
import pandas as pd
import subprocess
from rich import print as rprint
from rich.console import Console
from rich.progress import Progress
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config_utils import load_key
from core.all_whisper_methods.whisperX_utils import get_audio_duration
from core.all_tts_functions.tts_main import tts_main
import shutil
from pydub import AudioSegment

console = Console()

TEMP_DIR = 'output/audio/tmp'
SEGS_DIR = 'output/audio/segs'
TASKS_FILE = "output/audio/tts_tasks.xlsx"
OUTPUT_FILE = "output/audio/tts_tasks.xlsx"
TEMP_FILE_TEMPLATE = f"{TEMP_DIR}/{{}}_temp.wav"
OUTPUT_FILE_TEMPLATE = f"{SEGS_DIR}/{{}}.wav"

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(SEGS_DIR, exist_ok=True)

def parse_df_srt_time(time_str):
    hours, minutes, seconds = time_str.strip().split(':')
    seconds, milliseconds = seconds.split('.')
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000

def adjust_audio_speed(input_file, output_file, speed_factor):
    # 如果速度因子接近1，直接复制文件
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
            # 如果输出时长超过预期，但输入音频小于3秒，且误差在0.1秒内，就截取到预期长度
            if output_duration >= expected_duration * 1.01 and input_duration < 3 and diff <= 0.1:
                audio = AudioSegment.from_wav(output_file)
                trimmed_audio = audio[:(expected_duration * 1000)]  # pydub使用毫秒
                trimmed_audio.export(output_file, format="wav")
                print(f"截取到预期长度 {expected_duration:.2f} seconds")
                return
            elif output_duration >= expected_duration * 1.01:
                raise Exception(f"音频时长异常: 输入文件={input_file}, 输出文件={output_file}, 速度因子={speed_factor}, 输入时长={input_duration:.2f}s, 输出时长={output_duration:.2f}s")
            return
        except subprocess.CalledProcessError as e:
            if attempt < max_retries - 1:
                rprint(f"[yellow]调整音频速度失败,1秒后重试 ({attempt + 1}/{max_retries})[/yellow]")
                time.sleep(1)
            else:
                rprint(f"[red]调整音频速度失败,已达到最大重试次数 ({max_retries})[/red]")
                raise e

tasks_df = pd.read_excel(TASKS_FILE)




# gen tts
tasks_df['real_dur'] = 0
with Progress() as progress:
    task = progress.add_task("[cyan]生成TTS音频...", total=len(tasks_df))
    for index, row in tasks_df.iterrows():
        number = row['number']
        lines = eval(row['lines']) if isinstance(row['lines'], str) else row['lines']
        real_dur = 0
        for line_index, line in enumerate(lines):
            temp_file = TEMP_FILE_TEMPLATE.format(f"{number}_{line_index}")
            tts_main(line, temp_file, number, tasks_df)
            real_dur += get_audio_duration(temp_file)
        tasks_df.at[index, 'real_dur'] = real_dur
        progress.update(task, advance=1)



# merge by chunks
accept = load_key("speed_factor.accept")
min_speed = load_key("speed_factor.min")
chunk_start = 0
speed_var_error = 0.1 # 变速不精准 预留误差
tasks_df['new_sub_times'] = None
for index, row in tasks_df.iterrows():
    if row['cut_off'] == 1:
        # 把 chunk start 到 chunk end 新建成一个df
        chunk_df = tasks_df.iloc[chunk_start:index+1].reset_index(drop=True)
        chunk_durs = chunk_df['real_dur'].sum()
        tol_durs = chunk_df['tol_dur'].sum()
        durations = tol_durs - chunk_df.iloc[-1]['tolerance']
        all_gaps = chunk_df['gap'].sum() - chunk_df.iloc[-1]['gap']
        # 尽可能把原gap还原，检查加上gaps是否在允许范围内
        keep_gaps = True
        print(f"====Chunk {chunk_start} to {index} has duration {chunk_durs:.2f} seconds, tol_durs {tol_durs:.2f} seconds, all_gaps {all_gaps:.2f} seconds=====")
        # 最理想：能保留gaps，且能压在durs中不用tolerance
        if (chunk_durs + all_gaps) / accept < durations:
            speed_factor = max(min_speed, (chunk_durs + all_gaps) / (durations-speed_var_error))
        # 如果不能保留gaps，则检查能否压在durs中不用tolerance
        elif chunk_durs / accept < durations:
            speed_factor = max(min_speed, chunk_durs / (durations-speed_var_error))
            keep_gaps = False
        # 如果连durs都压不住，则只能用tolerance
        elif (chunk_durs + all_gaps) / accept < tol_durs:
            speed_factor = max(min_speed, (chunk_durs + all_gaps) / (tol_durs-speed_var_error))
        # 实在太快了，只能用tol_durs
        else:
            speed_factor = chunk_durs / (tol_durs-speed_var_error)
            keep_gaps = False
            if speed_factor > accept:
                print(f"Warning: Chunk {chunk_start} to {index} has duration {chunk_durs:.2f} seconds, speed factor is {speed_factor:.2f}, which is greater than accept {accept:.2f}")
        speed_factor = round(speed_factor, 3)

        # 开始处理标记新时间轴
        chunk_start_time = parse_df_srt_time(chunk_df.iloc[0]['start_time'])
        chunk_end_time = parse_df_srt_time(chunk_df.iloc[-1]['end_time']) + chunk_df.iloc[-1]['tolerance'] # 加上tolerance才是这一块的结束
        cur_time = chunk_start_time
        for i, row in chunk_df.iterrows():
            # 如果i不是0 也就是不是chunk的第一行 cur_time 需要加上上一行的gap 记得除以speed_factor
            if i != 0 and keep_gaps:
                cur_time += chunk_df.iloc[i-1]['gap']/speed_factor
            new_sub_times = []
            number = row['number']
            lines = eval(row['lines']) if isinstance(row['lines'], str) else row['lines']
            for line_index, line in enumerate(lines):
                # 开始变速 存为 OUTPUT_FILE_TEMPLATE
                temp_file = TEMP_FILE_TEMPLATE.format(f"{number}_{line_index}")
                output_file = OUTPUT_FILE_TEMPLATE.format(f"{number}_{line_index}")
                adjust_audio_speed(temp_file, output_file, speed_factor)
                ad_dur = get_audio_duration(output_file)
                new_sub_times.append([cur_time, cur_time+ad_dur])
                cur_time += ad_dur
            # 找到对应的主DataFrame索引并更新new_sub_times
            main_df_idx = tasks_df[tasks_df['number'] == row['number']].index[0]
            tasks_df.at[main_df_idx, 'new_sub_times'] = new_sub_times
        # 检查最后一行是否超出范围
        if cur_time > chunk_end_time:
            raise Exception(f"Chunk {chunk_start} to {index} exceeds the chunk end time {chunk_end_time:.2f} seconds with current time {cur_time:.2f} seconds")
        chunk_start = index+1

tasks_df.to_excel(OUTPUT_FILE, index=False)
