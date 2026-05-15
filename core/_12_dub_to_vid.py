import platform
import subprocess
import os

import cv2
import numpy as np
from rich.console import Console

from core._1_ytdlp import find_video_files
from core.asr_backend.audio_preprocess import normalize_audio_volume
from core.utils import *
from core.utils.models import *

console = Console()

DUB_VIDEO = "output/output_dub.mp4"
DUB_SUB_FILE = 'output/dub.srt'
DUB_ASS_FILE = 'output/dub.ass'
DUB_AUDIO = 'output/dub.mp3'

SRT_TRANS_DEFAULTS = {
    'fontname': 'Arial', 'fontsize': 17,
    'primary_color': '&H00FFFF', 'outline_color': '&H000000',
    'outline_width': 1, 'back_color': '&H33000000', 'border_style': 4,
    'alignment': 2, 'margin_v': 27,
}

def _platform_fontname():
    if platform.system() == 'Linux':
        return 'NotoSansCJK-Regular'
    elif platform.system() == 'Darwin':
        return 'Arial Unicode MS'
    return 'Arial'

def _build_dub_force_style():
    defaults = SRT_TRANS_DEFAULTS
    style = load_key("subtitle.ass_style.translation") or {}
    merged = {**defaults, **style}
    if 'fontname' not in style:
        merged['fontname'] = _platform_fontname()
    parts = [
        f"FontSize={merged['fontsize']}",
        f"FontName={merged['fontname']}",
        f"PrimaryColour={merged['primary_color']}",
        f"OutlineColour={merged['outline_color']}",
        f"OutlineWidth={merged['outline_width']}",
        f"BackColour={merged['back_color']}",
        f"Alignment={merged['alignment']}",
        f"MarginV={merged['margin_v']}",
        f"BorderStyle={merged['border_style']}",
    ]
    return ','.join(parts)

def _generate_dub_ass():
    from core.utils.ass_utils import generate_ass
    import pandas as pd

    style_config = load_key("subtitle.ass_style") or {}
    df, lines, new_sub_times = None, None, None

    from core._11_merge_audio import load_and_flatten_data
    df, lines, new_sub_times = load_and_flatten_data(_8_1_AUDIO_TASK)

    rows = []
    for i, ((start_time, end_time), line) in enumerate(zip(new_sub_times, lines)):
        rows.append({
            'timestamp': f"{int(start_time//3600):02d}:{int((start_time%3600)//60):02d}:{int(start_time%60):02d},{int((start_time*1000)%1000):03d} --> {int(end_time//3600):02d}:{int((end_time%3600)//60):02d}:{int(end_time%60):02d},{int((end_time*1000)%1000):03d}",
            'Translation': line,
        })
    df_ass = pd.DataFrame(rows)

    generate_ass(df_ass, ['Translation'], DUB_ASS_FILE, style_config)

def merge_video_audio():
    """Merge video and audio, and reduce video volume"""
    VIDEO_FILE = find_video_files()
    background_file = _BACKGROUND_AUDIO_FILE
    
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
    video = cv2.VideoCapture(VIDEO_FILE)
    TARGET_WIDTH = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    TARGET_HEIGHT = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    video.release()
    rprint(f"[bold green]Video resolution: {TARGET_WIDTH}x{TARGET_HEIGHT}[/bold green]")

    subtitle_format = load_key("subtitle.format") or 'srt'

    if subtitle_format == 'ass':
        if not os.path.exists(DUB_ASS_FILE):
            _generate_dub_ass()
        subtitle_filter = f"subtitles={DUB_ASS_FILE}"
    else:
        force_style = _build_dub_force_style()
        subtitle_filter = f"subtitles={DUB_SUB_FILE}:force_style='{force_style}'"
    
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