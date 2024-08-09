import os
import subprocess

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
    cmd = ['ffmpeg', '-i', video_file, '-i', background_file, '-i', original_vocal, '-i', audio_file, '-filter_complex', '[1:a]volume=1[a1];[2:a]volume=0.3[a2];[3:a]volume=1[a3];[a1][a2][a3]amix=inputs=3:duration=first:dropout_transition=3[a]', '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', output_file]

    try:
        subprocess.run(cmd, check=True)
        print(f"视频和音频已成功合并到 {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"合并视频和音频时出错: {e}")
    
    # 删除临时音频文件
    if os.path.exists('tmp_audio.wav'):
        os.remove('tmp_audio.wav')
        
# 测试
if __name__ == "__main__":
    merge_video_audio()