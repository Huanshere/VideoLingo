import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import glob
from yt_dlp import YoutubeDL

def download_video_ytdlp(url, save_path='output', resolution=1080):
    allowed_resolutions = [360, 480, 1080]
    if resolution not in allowed_resolutions:
        resolution = 1080
    
    os.makedirs(save_path, exist_ok=True)
    ydl_opts = {
        'format': f'bestvideo[height<={resolution}]+bestaudio/best[height<={resolution}]',
        'outtmpl': f'{save_path}/%(title)s.%(ext)s'
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def find_video_files(save_path='output'):
    from config import ALLOWED_VIDEO_FORMATS
    video_files = [file for file in glob.glob(save_path + "/*") if os.path.splitext(file)[1][1:] in ALLOWED_VIDEO_FORMATS]
    video_files = [file for file in video_files if not file.startswith("output/output")]
    # if num != 1, raise ValueError
    if len(video_files) != 1:
        raise ValueError(f"找到的视频数量不唯一，请检查。找到的视频数量: {len(video_files)}")
    return video_files[0]

if __name__ == '__main__':
    # 示例用法
    url = input('请输入您想下载的视频URL: ')
    resolution = input('请输入所需分辨率 (360/480/1080，默认1080): ')
    resolution = int(resolution) if resolution.isdigit() else 1080
    download_video_ytdlp(url, resolution=resolution)
    print(f"🎥 视频已下载到 {find_video_files()}")
