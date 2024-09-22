import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime
import pandas as pd
import subprocess
from pydub import AudioSegment

def time_to_datetime(time_str):
    return datetime.strptime(time_str, '%H:%M:%S.%f')

def create_silence(duration, output_file):
    subprocess.run([
        'ffmpeg', '-f', 'lavfi', '-i', f'anullsrc=channel_layout=mono:sample_rate=32000:duration={duration}',
        '-acodec', 'pcm_s16le', '-y', output_file
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def merge_all_audio():
    # 定义输入和输出路径
    input_excel = 'output/audio/sovits_tasks.xlsx'
    output_audio = 'output/trans_vocal_total.wav'
        
    df = pd.read_excel(input_excel)
    
    # 获取第一个音频文件的采样率
    first_audio = f'output/audio/segs/{df.iloc[0]["number"]}.wav'
    sample_rate = AudioSegment.from_wav(first_audio).frame_rate

    # 创建一个空的AudioSegment对象
    merged_audio = AudioSegment.silent(duration=0, frame_rate=sample_rate)

    prev_target_start_time = None
    prev_actual_duration = 0
    
    for index, row in df.iterrows():
        number = row['number']
        start_time = row['start_time']
        input_audio = f'output/audio/segs/{number}.wav'
        
        if not os.path.exists(input_audio):
            print(f"警告: 文件 {input_audio} 不存在,跳过此文件。")
            continue
        
        audio_segment = AudioSegment.from_wav(input_audio)
        actual_duration = len(audio_segment) / 1000  # 转换为秒
        target_start_time = time_to_datetime(start_time)
        
        silence_duration = (target_start_time - datetime(1900, 1, 1)).total_seconds() if prev_target_start_time is None else (target_start_time - prev_target_start_time).total_seconds() - prev_actual_duration
        
        if silence_duration > 0:
            silence = AudioSegment.silent(duration=int(silence_duration * 1000), frame_rate=sample_rate)
            merged_audio += silence
        
        merged_audio += audio_segment
        
        prev_target_start_time = target_start_time
        prev_actual_duration = actual_duration

    # 导出合并后的音频
    merged_audio.export(output_audio, format="wav")
    print(f"音频文件已成功拼接,输出文件: {output_audio}")

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
    
    from config import RESOLUTION
    if RESOLUTION == '0x0':
        print("Warning: A 0-second black video will be generated as a placeholder as Resolution is set to 0x0.")
        subprocess.run(['ffmpeg', '-f', 'lavfi', '-i', 'color=c=black:s=1920x1080:d=0',
                        '-c:v', 'libx264', '-t', '0', '-preset', 'ultrafast', '-y', output_file],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Placeholder video has been generated.")
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