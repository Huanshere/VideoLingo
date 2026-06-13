import os, subprocess, time, platform
from core._1_ytdlp import find_video_files
import cv2
import numpy as np
from core.utils import *
from core.utils.models import *

OUTPUT_DIR = "output"
OUTPUT_VIDEO = f"{OUTPUT_DIR}/output_sub.mp4"
SRC_SRT = f"{OUTPUT_DIR}/src.srt"
TRANS_SRT = f"{OUTPUT_DIR}/trans.srt"
SRC_ASS = f"{OUTPUT_DIR}/src.ass"
TRANS_ASS = f"{OUTPUT_DIR}/trans.ass"

SRT_SRC_DEFAULTS = {
    'fontname': 'Arial', 'fontsize': 15,
    'primary_color': '&HFFFFFF', 'outline_color': '&H000000',
    'outline_width': 1.0, 'shadow_color': '&H80000000', 'border_style': 1,
    'alignment': 8, 'margin_v': 10, 'margin_l': 10, 'margin_r': 10,
}
SRT_TRANS_DEFAULTS = {
    'fontname': 'Arial', 'fontsize': 17,
    'primary_color': '&H00FFFF', 'outline_color': '&H000000',
    'outline_width': 1.0, 'back_color': '&H33000000', 'border_style': 4,
    'alignment': 2, 'margin_v': 27, 'margin_l': 10, 'margin_r': 10,
}

def _platform_fontname():
    if platform.system() == 'Linux':
        return 'NotoSansCJK-Regular'
    elif platform.system() == 'Darwin':
        return 'Arial Unicode MS'
    return 'Arial'

def _build_srt_force_style(style_key):
    defaults = SRT_SRC_DEFAULTS if style_key == 'source' else SRT_TRANS_DEFAULTS
    config_key = f"subtitle.srt_style.{style_key}"
    style = load_key(config_key) or {}
    merged = {**defaults, **style}
    if 'fontname' not in style:
        merged['fontname'] = _platform_fontname()
    parts = [
        f"FontSize={merged['fontsize']}",
        f"FontName={merged['fontname']}",
        f"PrimaryColour={merged['primary_color']}",
        f"OutlineColour={merged['outline_color']}",
        f"OutlineWidth={merged['outline_width']}",
    ]
    if style_key == 'source':
        parts.append(f"ShadowColour={merged['shadow_color']}")
        parts.append(f"BorderStyle={merged['border_style']}")
    else:
        parts.append(f"BackColour={merged['back_color']}")
        parts.append(f"Alignment={merged['alignment']}")
        parts.append(f"MarginV={merged['margin_v']}")
        parts.append(f"BorderStyle={merged['border_style']}")
    return ','.join(parts)

def check_gpu_available():
    try:
        result = subprocess.run(['ffmpeg', '-encoders'], capture_output=True, text=True)
        return 'h264_nvenc' in result.stdout
    except:
        return False

def merge_subtitles_to_video():
    video_file = find_video_files()
    os.makedirs(os.path.dirname(OUTPUT_VIDEO), exist_ok=True)

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

    subtitle_format = load_key("subtitle.format") or 'srt'

    video = cv2.VideoCapture(video_file)
    TARGET_WIDTH = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    TARGET_HEIGHT = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    video.release()
    rprint(f"[bold green]Video resolution: {TARGET_WIDTH}x{TARGET_HEIGHT}[/bold green]")

    if subtitle_format == 'ass':
        if not os.path.exists(SRC_ASS) or not os.path.exists(TRANS_ASS):
            rprint("ASS subtitle files not found in the 'output' directory.")
            exit(1)

        src_style = f"subtitles={SRC_ASS}"
        trans_style = f"subtitles={TRANS_ASS}"
    else:
        if not os.path.exists(SRC_SRT) or not os.path.exists(TRANS_SRT):
            rprint("Subtitle files not found in the 'output' directory.")
            exit(1)

        src_force = _build_srt_force_style('source')
        trans_force = _build_srt_force_style('translation')
        src_style = f"subtitles={SRC_SRT}:force_style='{src_force}'"
        trans_style = f"subtitles={TRANS_SRT}:force_style='{trans_force}'"

    ffmpeg_cmd = [
        'ffmpeg', '-i', video_file,
        '-vf', (
            f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2,"
            f"{src_style},"
            f"{trans_style}"
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