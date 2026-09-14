import os,sys
import glob
import json
import re
import subprocess
from core.utils import *

OUTPUT_DIR = "output"
INPUT_MANIFEST = "input_manifest.json"
GENERATED_AUDIO_NAMES = {"dub.mp3", "normalized_dub.wav"}
GENERATED_VIDEO_NAMES = {"output_sub.mp4", "output_dub.mp4"}

def sanitize_filename(filename):
    # Remove or replace illegal characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Ensure filename doesn't start or end with a dot or space
    filename = filename.strip('. ')
    # Use default name if filename is empty
    return filename if filename else 'video'

def update_ytdlp():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
        if 'yt_dlp' in sys.modules:
            del sys.modules['yt_dlp']
        rprint("[green]yt-dlp updated[/green]")
    except subprocess.CalledProcessError as e:
        rprint("[yellow]Warning: Failed to update yt-dlp: {e}[/yellow]")
    from yt_dlp import YoutubeDL
    return YoutubeDL

def download_video_ytdlp(url, save_path='output', resolution='1080'):
    os.makedirs(save_path, exist_ok=True)
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best' if resolution == 'best' else f'bestvideo[height<={resolution}]+bestaudio/best[height<={resolution}]',
        'outtmpl': f'{save_path}/%(title)s.%(ext)s',
        'noplaylist': True,
        'writethumbnail': True,
        'merge_output_format': 'mp4',
        'postprocessors': [{'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg'}],
    }

    # None/missing inherits yt-dlp's system/environment proxy discovery.
    # An empty string explicitly disables proxies; a URL overrides discovery.
    youtube = load_key("youtube")
    proxy = youtube.get("proxy")
    if proxy is not None:
        if not isinstance(proxy, str):
            raise ValueError('youtube.proxy must be null, an empty string, or a proxy URL')
        ydl_opts['proxy'] = proxy.strip()

    # Read Youtube Cookie File
    cookies_path = load_key("youtube.cookies_path")
    if os.path.exists(cookies_path):
        ydl_opts["cookiefile"] = str(cookies_path)

    # Get YoutubeDL class after updating
    YoutubeDL = update_ytdlp()
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    # Check and rename files after download
    for file in os.listdir(save_path):
        if os.path.isfile(os.path.join(save_path, file)):
            filename, ext = os.path.splitext(file)
            new_filename = sanitize_filename(filename)
            if new_filename != filename:
                os.rename(os.path.join(save_path, file), os.path.join(save_path, new_filename + ext))
    media_file = find_video_files(save_path)
    write_input_manifest(media_file, "video", save_path)

def write_input_manifest(media_file: str, media_type: str, save_path='output'):
    os.makedirs(save_path, exist_ok=True)
    manifest_path = os.path.join(save_path, INPUT_MANIFEST)
    media_path = media_file.replace("\\", "/") if sys.platform.startswith('win') else media_file
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({"path": media_path, "type": media_type}, f, ensure_ascii=False, indent=2)

def _read_input_manifest(save_path='output'):
    manifest_path = os.path.join(save_path, INPUT_MANIFEST)
    if not os.path.exists(manifest_path):
        return None
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    media_file = data.get("path")
    media_type = data.get("type")
    if media_type not in {"video", "audio"} or not media_file or not os.path.exists(media_file):
        return None
    return media_file.replace("\\", "/") if sys.platform.startswith('win') else media_file, media_type

def find_video_files(save_path='output'):
    video_files = [file for file in glob.glob(save_path + "/*") if os.path.isfile(file) and os.path.splitext(file)[1][1:].lower() in load_key("allowed_video_formats")]
    # change \\ to /, this happen on windows
    if sys.platform.startswith('win'):
        video_files = [file.replace("\\", "/") for file in video_files]
    video_files = [
        file
        for file in video_files
        if os.path.basename(file).lower() not in GENERATED_VIDEO_NAMES
    ]
    if len(video_files) != 1:
        raise ValueError(f"Number of videos found {len(video_files)} is not unique. Please check.")
    return video_files[0]

def find_audio_files(save_path='output'):
    audio_files = [file for file in glob.glob(save_path + "/*") if os.path.splitext(file)[1][1:].lower() in load_key("allowed_audio_formats")]
    if sys.platform.startswith('win'):
        audio_files = [file.replace("\\", "/") for file in audio_files]
    audio_files = [file for file in audio_files if os.path.basename(file) not in GENERATED_AUDIO_NAMES]
    if len(audio_files) != 1:
        raise ValueError(f"Number of audio files found {len(audio_files)} is not unique. Please check.")
    return audio_files[0]

def _safe_find_video_file(save_path='output'):
    try:
        return find_video_files(save_path)
    except ValueError as e:
        if "found 0" in str(e):
            return None
        raise

def _safe_find_audio_file(save_path='output'):
    try:
        return find_audio_files(save_path)
    except ValueError as e:
        if "found 0" in str(e):
            return None
        raise

def find_media_file(save_path='output'):
    manifest = _read_input_manifest(save_path)
    if manifest:
        return manifest
    video_file = _safe_find_video_file(save_path)
    if video_file:
        return video_file, "video"
    audio_file = _safe_find_audio_file(save_path)
    if audio_file:
        return audio_file, "audio"
    raise ValueError("No media file found. Please download or upload a media file first.")

def is_audio_only_input(save_path='output'):
    # True when the input is a standalone audio file (no video present).
    # In this case VideoLingo only produces subtitle files; no video output.
    try:
        _, media_type = find_media_file(save_path)
        return media_type == "audio"
    except Exception:
        return False

if __name__ == '__main__':
    # Example usage
    url = input('Please enter the URL of the video you want to download: ')
    resolution = input('Please enter the desired resolution (360/480/720/1080, default 1080): ')
    resolution = int(resolution) if resolution.isdigit() else 1080
    download_video_ytdlp(url, resolution=resolution)
    print(f"🎥 Video has been downloaded to {find_video_files()}")
