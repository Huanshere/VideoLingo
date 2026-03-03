import os, subprocess, time
from core._1_ytdlp import find_video_files
import cv2
import numpy as np
import platform
from core.utils import *
import requests
import shutil 
from core.capcut_process.request_capcut_api import create_draft, add_video_impl, add_subtitle, save_draft


SRC_FONT_SIZE = 15
TRANS_FONT_SIZE = 17
FONT_NAME = 'Arial'
TRANS_FONT_NAME = 'Arial'

# Linux need to install google noto fonts: apt-get install fonts-noto
if platform.system() == 'Linux':
    FONT_NAME = 'NotoSansCJK-Regular'
    TRANS_FONT_NAME = 'NotoSansCJK-Regular'
# Mac OS has different font names
elif platform.system() == 'Darwin':
    FONT_NAME = 'Arial Unicode MS'
    TRANS_FONT_NAME = 'Arial Unicode MS'

SRC_FONT_COLOR = '&HFFFFFF'
SRC_OUTLINE_COLOR = '&H000000'
SRC_OUTLINE_WIDTH = 1
SRC_SHADOW_COLOR = '&H80000000'
TRANS_FONT_COLOR = '&H00FFFF'
TRANS_OUTLINE_COLOR = '&H000000'
TRANS_OUTLINE_WIDTH = 1 
TRANS_BACK_COLOR = '&H33000000'

OUTPUT_DIR = "output"
OUTPUT_VIDEO = f"{OUTPUT_DIR}/output_sub.mp4"
SRC_SRT = f"{OUTPUT_DIR}/src.srt"
TRANS_SRT = f"{OUTPUT_DIR}/trans.srt"
    
def check_gpu_available():
    try:
        result = subprocess.run(['ffmpeg', '-encoders'], capture_output=True, text=True)
        return 'h264_nvenc' in result.stdout
    except:
        return False

def create_capcut_draft(video_file, TARGET_WIDTH, TARGET_HEIGHT):
    # 从配置文件读取草稿目录路径
    draft_folder = load_key("capcut.draft_folder")
    response = create_draft(TARGET_WIDTH, TARGET_HEIGHT)
    print(f"create_draft:{response}")

    # 获取草稿id
    draft_data = response
    draft_id = draft_data["output"]["draft_id"]
    
    # 保存draft_id到配置文件，以便其他文件使用
    update_key("capcut.trans_draft_id", draft_id)
    
    # 添加原始视频
    add_video_response = add_video_impl(
        video_url=os.path.abspath(video_file),
        draft_id=draft_id
    )
    print(f"add_video_response:{add_video_response}")

    # 从配置文件读取原始文本设置
    orig_text_config = load_key("capcut.orig_text")
    
    # 添加原始字幕
    add_srt_response = add_subtitle(
        srt=os.path.abspath(SRC_SRT),
        track_name="src_srt",
        draft_id=draft_id,
        font = orig_text_config["font"],
        font_size=orig_text_config["font_size"],
        font_color=orig_text_config["color"],
        border_color=orig_text_config["stroke_color"] if orig_text_config["stroke"] else None,
        border_width=orig_text_config["stroke_width"] if orig_text_config["stroke"] else 0,
        transform_y=orig_text_config["y_offset"]
    )
    print(add_srt_response)

    # 从配置文件读取翻译文本设置
    trans_text_config = load_key("capcut.trans_text")
    
    # 添加翻译字幕
    add_srt_response = add_subtitle(
        srt=os.path.abspath(TRANS_SRT),
        track_name="trans_srt",
        draft_id=draft_id,
        font = trans_text_config["font"],
        font_size=trans_text_config["font_size"],
        font_color=trans_text_config["color"],
        border_color=trans_text_config["stroke_color"] if trans_text_config["stroke"] else None,
        border_width=trans_text_config["stroke_width"] if trans_text_config["stroke"] else 0,
        transform_y=trans_text_config["y_offset"]
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

def merge_subtitles_to_video():
    video_file = find_video_files()
    os.makedirs(os.path.dirname(OUTPUT_VIDEO), exist_ok=True)

    video = cv2.VideoCapture(video_file)
    TARGET_WIDTH = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    TARGET_HEIGHT = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    video.release()

    # 创建剪映草稿
    if load_key("capcut.enable_export"):
        create_capcut_draft(video_file, TARGET_WIDTH, TARGET_HEIGHT)

    # Check resolution
    if not load_key("burn_subtitles"):
        rprint("[bold yellow]Warning: A 0-second black video will be generated as a placeholder as subtitles are not burned in.[/bold yellow]")

        # Create a black frame
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(OUTPUT_VIDEO, fourcc, 1, (1920, 1080))
        out.write(frame)
        out.release()

        rprint("[bold green]Placeholder video has been generated.[/bold green]")
        return

    if not os.path.exists(SRC_SRT) or not os.path.exists(TRANS_SRT):
        rprint("Subtitle files not found in the 'output' directory.")
        exit(1)

    rprint(f"[bold green]Video resolution: {TARGET_WIDTH}x{TARGET_HEIGHT}[/bold green]")
    ffmpeg_cmd = [
        'ffmpeg', '-i', video_file,
        '-vf', (
            f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2,"
            f"subtitles={SRC_SRT}:force_style='FontSize={SRC_FONT_SIZE},FontName={FONT_NAME}," 
            f"PrimaryColour={SRC_FONT_COLOR},OutlineColour={SRC_OUTLINE_COLOR},OutlineWidth={SRC_OUTLINE_WIDTH},"
            f"ShadowColour={SRC_SHADOW_COLOR},BorderStyle=1',"
            f"subtitles={TRANS_SRT}:force_style='FontSize={TRANS_FONT_SIZE},FontName={TRANS_FONT_NAME},"
            f"PrimaryColour={TRANS_FONT_COLOR},OutlineColour={TRANS_OUTLINE_COLOR},OutlineWidth={TRANS_OUTLINE_WIDTH},"
            f"BackColour={TRANS_BACK_COLOR},Alignment=2,MarginV=27,BorderStyle=4'"
        ).encode('utf-8'),
    ]

    ffmpeg_gpu = load_key("ffmpeg_gpu")
    if ffmpeg_gpu:
        rprint("[bold green]will use GPU acceleration.[/bold green]")
        ffmpeg_cmd.extend(['-c:v', 'h264_nvenc'])
    ffmpeg_cmd.extend(['-y', OUTPUT_VIDEO])

    rprint("🎬 Start merging subtitles to video...")
    start_time = time.time()
    process = subprocess.Popen(ffmpeg_cmd)

    try:
        process.wait()
        if process.returncode == 0:
            rprint(f"\n✅ Done! Time taken: {time.time() - start_time:.2f} seconds")
        else:
            rprint("\n❌ FFmpeg execution error")
    except Exception as e:
        rprint(f"\n❌ Error occurred: {e}")
        if process.poll() is None:
            process.kill()

if __name__ == "__main__":
    merge_subtitles_to_video()