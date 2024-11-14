import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import subprocess
from pydub import AudioSegment
from rich import print as rprint

INPUT_EXCEL = 'output/audio/tts_tasks.xlsx'
OUTPUT_AUDIO = 'output/trans_vocal_total.wav'

DUB_SUB_FILE = 'output/dub_sub.srt'
SEGS_DIR = 'output/audio/segs'
OUTPUT_FILE_TEMPLATE = f"{SEGS_DIR}/{{}}.wav"

# read INPUT_EXCEL
df = pd.read_excel(INPUT_EXCEL)
# 关注 lines 和 new_sub_times，需要先 eval 解析字符串，再展平二维数组
lines = [eval(line) if isinstance(line, str) else line for line in df['lines'].tolist()]
lines = [item for sublist in lines for item in sublist]  # 展平二维数组

new_sub_times = [eval(time) if isinstance(time, str) else time for time in df['new_sub_times'].tolist()]
new_sub_times = [item for sublist in new_sub_times for item in sublist]  # 展平二维数组

# 构建 audios 数组
audios = []
current_idx = 0
for index, row in df.iterrows():
    number = row['number']
    line_count = len(eval(row['lines']) if isinstance(row['lines'], str) else row['lines'])
    for line_index in range(line_count):
        temp_file = OUTPUT_FILE_TEMPLATE.format(f"{number}_{line_index}")
        audios.append(temp_file)
        current_idx += 1

print(lines)
print(new_sub_times)
print(audios)

def format_time(seconds):
    """将秒数转换为 SRT 时间格式 (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"

def create_srt_subtitle():
    """根据 lines 和 new_sub_times 生成 SRT 格式字幕文件"""
    srt_content = []
    
    for i, (line, time_range) in enumerate(zip(lines, new_sub_times), 1):
        start_time, end_time = time_range
        srt_entry = (
            f"{i}\n"
            f"{format_time(start_time)} --> {format_time(end_time)}\n"
            f"{line}\n"
        )
        srt_content.append(srt_entry)
    
    # 将字幕内容写入文件
    with open(DUB_SUB_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(srt_content))
    
    rprint(f"[bold green]Successfully generated subtitle file: {DUB_SUB_FILE}[/bold green]")

create_srt_subtitle()

def merge_all_audio():
    # 获取第一个音频文件的采样率
    first_audio = audios[0]
    
    # 添加文件检查
    if not os.path.exists(first_audio):
        rprint(f"[bold red]Error: First audio file {first_audio} does not exist![/bold red]")
        return
        
    print(f"Trying to open: {first_audio}")  # 打印正在尝试打开的文件路径
    sample_rate = AudioSegment.from_wav(first_audio).frame_rate

    # 创建空的 AudioSegment 对象
    merged_audio = AudioSegment.silent(duration=0, frame_rate=sample_rate)

    for i, (audio_file, time_range) in enumerate(zip(audios, new_sub_times)):
        if not os.path.exists(audio_file):
            rprint(f"[bold yellow]Warning: File {audio_file} does not exist, skipping this file.[/bold yellow]")
            continue
        
        # 使用 ffmpeg 重新采样音频文件到临时文件
        temp_file = f"{audio_file}_temp.wav"
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-i', audio_file,
            '-ar', str(sample_rate),  # 设置采样率
            '-ac', '1',  # 设置为单声道
            '-acodec', 'pcm_s16le',  # 设置编码格式
            temp_file
        ]
        subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 读取重新采样后的音频
        audio_segment = AudioSegment.from_wav(temp_file)
        start_time, end_time = time_range
        
        # 如果不是第一个片段，计算与前一个片段之间需要的静音时长
        if i > 0:
            prev_end = new_sub_times[i-1][1]
            silence_duration = start_time - prev_end
            if silence_duration > 0:
                silence = AudioSegment.silent(duration=int(silence_duration * 1000), frame_rate=sample_rate)
                merged_audio += silence
        else:
            # 第一个片段，如果开始时间不是0，添加初始静音
            if start_time > 0:
                silence = AudioSegment.silent(duration=int(start_time * 1000), frame_rate=sample_rate)
                merged_audio += silence
        
        merged_audio += audio_segment
        
        # 删除临时文件
        os.remove(temp_file)

    # 导出合并后的音频
    merged_audio.export(OUTPUT_AUDIO, format="wav")
    rprint(f"[bold green]Audio file successfully merged, output file: {OUTPUT_AUDIO}[/bold green]")
    
if __name__ == "__main__":
    merge_all_audio()