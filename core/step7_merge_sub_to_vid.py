import os, glob, subprocess, time

EN_FONT_SIZE = 16
TRANS_FONT_SIZE = 18
FONT_NAME = 'Arial'
TRANS_FONT_NAME = 'Arial'
EN_FONT_COLOR = '&HFFFFFF' 
EN_OUTLINE_COLOR = '&H000000'
EN_OUTLINE_WIDTH = 1
EN_SHADOW_COLOR = '&H80000000'
TRANS_FONT_COLOR = '&H00FFFF'
TRANS_OUTLINE_COLOR = '&H000000'
TRANS_OUTLINE_WIDTH = 1 
TRANS_BACK_COLOR = '&H33000000'

TARGET_WIDTH = 854
TARGET_HEIGHT = 480 # for demo only 480p


def merge_subtitles_to_video(video_file, use_gpu=False):
    input_video = video_file
    output_video = "output/output_with_subtitles.mp4"
    en_srt = "output/english_subtitles.srt"
    trans_srt = "output/translated_subtitles.srt"

    print(f"输入视频: {input_video}")
    print(f"输出视频: {output_video}")
    print(f"英文字幕: {en_srt}")
    print(f"翻译字幕: {trans_srt}")

    if not os.path.exists(en_srt) or not os.path.exists(trans_srt):
        print("字幕文件在'output'目录中未找到。")
        return False

    if not os.path.exists(input_video):
        print(f"输入视频文件 {input_video} 不存在。")
        return False

    os.makedirs(os.path.dirname(output_video), exist_ok=True)

    ffmpeg_cmd = [
        'ffmpeg', '-i', video_file,
        '-vf', (
            f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2,"
            f"subtitles={en_srt}:force_style='FontSize={EN_FONT_SIZE},FontName={FONT_NAME}," 
            f"PrimaryColour={EN_FONT_COLOR},OutlineColour={EN_OUTLINE_COLOR},OutlineWidth={EN_OUTLINE_WIDTH},"
            f"ShadowColour={EN_SHADOW_COLOR},BorderStyle=1',"
            f"subtitles={trans_srt}:force_style='FontSize={TRANS_FONT_SIZE},FontName={TRANS_FONT_NAME},"
            f"PrimaryColour={TRANS_FONT_COLOR},OutlineColour={TRANS_OUTLINE_COLOR},OutlineWidth={TRANS_OUTLINE_WIDTH},"
            f"BackColour={TRANS_BACK_COLOR},Alignment=2,MarginV=25,BorderStyle=4'"
        ),
        '-y',
        output_video
    ]

    if use_gpu:
        ffmpeg_cmd.insert(1, '-hwaccel')
        ffmpeg_cmd.insert(2, 'cuda')
        ffmpeg_cmd.extend(['-c:v', 'h264_nvenc', '-preset', 'p4', '-crf', '23'])
    else:
        ffmpeg_cmd.extend(['-c:v', 'libx264', '-preset', 'medium', '-crf', '23'])

    ffmpeg_cmd.extend(['-c:a', 'aac', '-b:a', '128k'])

    print(f"执行的FFmpeg命令: {' '.join(ffmpeg_cmd)}")

    try:
        result = subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
        print("FFmpeg输出:")
        print(result.stdout)
        print("FFmpeg错误输出:")
        print(result.stderr)
        print("字幕已成功合并到视频中。")
        return True
    except subprocess.CalledProcessError as e:
        print(f"合并字幕时发生错误：{e}")
        print(f"FFmpeg输出：{e.output}")
        print(f"FFmpeg错误输出：{e.stderr}")
        return False

# ... 其余代码保持不变 ...

if __name__ == "__main__":
    merge_subtitles_to_video()
