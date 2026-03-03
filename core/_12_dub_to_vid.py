import platform
import subprocess
import os
import shutil

import cv2
import numpy as np
import requests
from rich.console import Console

from core._1_ytdlp import find_video_files
from core.asr_backend.audio_preprocess import normalize_audio_volume
from core.utils import *
from core.utils.models import *
from core.capcut_process.request_capcut_api import create_draft, add_video_impl, add_audio_track, add_subtitle, save_draft

from core._11_merge_audio import load_and_flatten_data, get_audio_files

console = Console()

DUB_VIDEO = "output/output_dub.mp4"
DUB_SUB_FILE = 'output/dub.srt'
DUB_AUDIO = 'output/dub.mp3'

TRANS_FONT_SIZE = 17
TRANS_FONT_NAME = 'Arial'
if platform.system() == 'Linux':
    TRANS_FONT_NAME = 'NotoSansCJK-Regular'
if platform.system() == 'Darwin':
    TRANS_FONT_NAME = 'Arial Unicode MS'

TRANS_FONT_COLOR = '&H00FFFF'
TRANS_OUTLINE_COLOR = '&H000000'
TRANS_OUTLINE_WIDTH = 1 
TRANS_BACK_COLOR = '&H33000000'

def create_capcut_draft(video_file, TARGET_WIDTH, TARGET_HEIGHT):
    # 创建一个空白草稿
    draft_folder = "/Users/sunguannan/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
    draft_data = create_draft(TARGET_WIDTH, TARGET_HEIGHT)
    print(draft_data)

    # 获取草稿id
    draft_id = draft_data["output"]["draft_id"]
    
    # 保存draft_id到配置文件，以便其他文件使用
    update_key("capcut.dub_draft_id", draft_id)
    
    # 添加原始视频
    add_video_response = add_video_impl(
        video_url=os.path.abspath(video_file),
        draft_id=draft_id
    )
    print(add_video_response)
    
    # 获取音频文件列表和时间信息
    df, lines, new_sub_times = load_and_flatten_data(_8_1_AUDIO_TASK)
    audios = get_audio_files(df)
    
    # 添加每个音频片段到草稿中
    for i, (audio_file, time_range) in enumerate(zip(audios, new_sub_times)):
        if not os.path.exists(audio_file):
            print(f"警告：音频文件 {audio_file} 不存在，跳过...")
            continue
            
        start_time, end_time = time_range
        duration = end_time - start_time
        
        # 添加音频到草稿
        add_audio_response = add_audio_track(
            audio_url=os.path.abspath(audio_file),
            start=0,  # 音频文件的起始时间
            end=duration,  # 音频文件的结束时间
            target_start=start_time,  # 设置音频在时间线上的起始位置
            volume=1.0,  # 设置音量
            track_name="dub_tracks",  # 为每个音频片段创建单独的轨道
            draft_id=draft_id
        )
        print(f"添加音频 {audio_file} 结果:", add_audio_response)
    
    # 添加dub字幕
    # 从配置文件中获取配音文本设置
    dub_font = load_key("capcut.dub_text.font")
    dub_font_size = load_key("capcut.dub_text.font_size")
    dub_color = load_key("capcut.dub_text.color")
    dub_stroke = load_key("capcut.dub_text.stroke")
    dub_stroke_color = load_key("capcut.dub_text.stroke_color")
    dub_stroke_width = load_key("capcut.dub_text.stroke_width")
    dub_y_offset = load_key("capcut.dub_text.y_offset")
    
    add_srt_response = add_subtitle(
        srt=os.path.abspath(DUB_SUB_FILE),
        track_name="src_srt",
        draft_id=draft_id,
        font=dub_font,
        font_size=dub_font_size,
        font_color=dub_color,
        border_color=dub_stroke_color if dub_stroke else None,
        border_width=dub_stroke_width if dub_stroke else 0,
        transform_y=dub_y_offset
    )
    print(add_srt_response)

    # 保存草稿
    save_response = save_draft(draft_id, draft_folder)
    print("保存草稿结果:", save_response)
    
    # 复制草稿文件夹到指定目录
    source_draft_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "core/capcut_api", draft_id)
    target_draft_dir = os.path.join(draft_folder, draft_id)
    
    if os.path.exists(source_draft_dir):
        # 如果目标目录已存在，先删除
        if os.path.exists(target_draft_dir):
            print(f"目标文件夹 {target_draft_dir} 已存在，正在删除...")
            shutil.rmtree(target_draft_dir)
        
        # 复制文件夹
        print(f"正在将草稿文件夹从 {source_draft_dir} 复制到 {target_draft_dir}...")
        shutil.move(source_draft_dir, target_draft_dir)
        print(f"草稿文件夹复制完成")
    else:
        print(f"警告：源草稿文件夹 {source_draft_dir} 不存在")
    
    return draft_id

def merge_video_audio():
    """Merge video and audio, and reduce video volume"""
    VIDEO_FILE = find_video_files()
    background_file = _BACKGROUND_AUDIO_FILE

    video = cv2.VideoCapture(VIDEO_FILE)
    TARGET_WIDTH = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    TARGET_HEIGHT = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    video.release()

    # 创建剪映草稿
    if load_key("capcut.enable_export"):
        create_capcut_draft(VIDEO_FILE, TARGET_WIDTH, TARGET_HEIGHT)
    
    if not load_key("burn_subtitles"):
        rprint("[bold yellow]Warning: A 0-second black video will be generated as a placeholder as subtitles are not burned in.[/bold yellow]")

        # Create a black frame
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(DUB_VIDEO, fourcc, 1, (1920, 1080))
        out.write(frame)
        out.release()

        rprint("[bold green]Placeholder video has been generated.[/bold green]")
        return

    # Normalize dub audio
    normalized_dub_audio = 'output/normalized_dub.wav'
    normalize_audio_volume(DUB_AUDIO, normalized_dub_audio)
    
    # Merge video and audio with translated subtitles
    rprint(f"[bold green]Video resolution: {TARGET_WIDTH}x{TARGET_HEIGHT}[/bold green]")
    
    subtitle_filter = (
        f"subtitles={DUB_SUB_FILE}:force_style='FontSize={TRANS_FONT_SIZE},"
        f"FontName={TRANS_FONT_NAME},PrimaryColour={TRANS_FONT_COLOR},"
        f"OutlineColour={TRANS_OUTLINE_COLOR},OutlineWidth={TRANS_OUTLINE_WIDTH},"
        f"BackColour={TRANS_BACK_COLOR},Alignment=2,MarginV=27,BorderStyle=4'"
    )
    
    cmd = [
        'ffmpeg', '-y', '-i', VIDEO_FILE, '-i', background_file, '-i', normalized_dub_audio,
        '-filter_complex',
        f'[0:v]scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease,'
        f'pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2,'
        f'{subtitle_filter}[v];'
        f'[1:a][2:a]amix=inputs=2:duration=first:dropout_transition=3[a]'
    ]

    if load_key("ffmpeg_gpu"):
        rprint("[bold green]Using GPU acceleration...[/bold green]")
        cmd.extend(['-map', '[v]', '-map', '[a]', '-c:v', 'h264_nvenc'])
    else:
        cmd.extend(['-map', '[v]', '-map', '[a]'])
    
    cmd.extend(['-c:a', 'aac', '-b:a', '96k', DUB_VIDEO])
    
    subprocess.run(cmd)
    rprint(f"[bold green]Video and audio successfully merged into {DUB_VIDEO}[/bold green]")

if __name__ == '__main__':
    merge_video_audio()
