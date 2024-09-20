
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime
import librosa
import pandas as pd
import subprocess

def time_to_datetime(time_str):
    return datetime.strptime(time_str, '%H:%M:%S.%f')

def create_silence(duration, output_file):
    subprocess.run([
        'ffmpeg', '-f', 'lavfi', '-i', f'anullsrc=channel_layout=mono:sample_rate=32000:duration={duration}',
        '-acodec', 'pcm_s16le', '-y', output_file
    ], check=True)

def merge_all_audio():
    # 定义输入和输出路径
    input_excel = 'output/audio/sovits_tasks.xlsx'
    output_audio = 'output/trans_vocal_total.wav'
        
    df = pd.read_excel(input_excel)
    temp_file = r'output/audio/tmp/temp_file_list.txt' 

    with open(temp_file, 'w') as f:
        prev_target_start_time = None
        prev_actual_duration = 0
        
        for index, row in df.iterrows():
            number = row['number']
            start_time = row['start_time']
            input_audio = f'output/audio/segs/{number}.wav'
            
            if not os.path.exists(input_audio):
                print(f"警告: 文件 {input_audio} 不存在,跳过此文件。")
                continue
            
            y, sr = librosa.load(input_audio)  
            actual_duration = librosa.get_duration(y=y, sr=sr)
            target_start_time = time_to_datetime(start_time)
            
            silence_duration = (target_start_time - datetime(1900, 1, 1)).total_seconds() if prev_target_start_time is None else (target_start_time - prev_target_start_time).total_seconds() - prev_actual_duration
            
            if silence_duration > 0:
                silence_file = f'output/audio/tmp/silence_{index}.wav'
                create_silence(silence_duration, silence_file) 
                f.write(f"file '{os.path.abspath(silence_file)}'\n")
            
            f.write(f"file '{os.path.abspath(input_audio)}'\n")
            
            prev_target_start_time = target_start_time
            prev_actual_duration = actual_duration

    ffmpeg_cmd = [    
        'ffmpeg', '-f', 'concat', '-safe', '0', 
        '-i', os.path.abspath(temp_file), '-c', 'copy', os.path.abspath(output_audio)
    ]

    if os.path.exists(output_audio):
        os.remove(output_audio)

    print("开始拼接音频文件...")
    try:
        subprocess.run(ffmpeg_cmd, check=True, stderr=subprocess.PIPE)
        print(f"音频文件已成功拼接,输出文件: {output_audio}")  
    except subprocess.CalledProcessError as e:
        print(f"错误: FFmpeg命令执行失败。\n{e.stderr.decode()}")

    os.remove(temp_file)
    for file in os.listdir('output/audio/tmp'):
        if file.startswith('silence_'):
            os.remove(os.path.join('output/audio/tmp', file))  
    print("临时文件已删除。")

def merge_video_audio():
    """将视频和音频合并,并减小视频音量"""
    video_file = "output/output_video_with_subs.mp4"
    background_file = 'output/audio/background.wav'
    original_vocal = 'output/audio/original_vocal.wav'
    audio_file = "output/trans_vocal_total.wav"    
    output_file = "output/output_video_with_audio.mp4"

    if os.path.exists(output_file):
        print(f"{output_file} 文件已存在,跳过处理。")
        return

    # 合并视频和音频
    from config import ORIGINAL_VOLUME
    volumn = ORIGINAL_VOLUME
    cmd = ['ffmpeg', '-i', video_file, '-i', background_file, '-i', original_vocal, '-i', audio_file, '-filter_complex', f'[1:a]volume=1[a1];[2:a]volume={volumn}[a2];[3:a]volume=1[a3];[a1][a2][a3]amix=inputs=3:duration=first:dropout_transition=3[a]', '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', output_file]

    try:
        subprocess.run(cmd, check=True)
        print(f"视频和音频已成功合并到 {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"合并视频和音频时出错: {e}")
    
    # 删除临时音频文件
    if os.path.exists('tmp_audio.wav'):
        os.remove('tmp_audio.wav')

def merge_main():
    merge_all_audio()
    merge_video_audio()
    
if __name__ == "__main__":
    merge_main()