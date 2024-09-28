import os
import sys
from yt_dlp import YoutubeDL
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import YTB_RESOLUTION

def download_videos_from_channel(channel_url, start_date, resolution=YTB_RESOLUTION, save_path='D:\\20.my-gptpilot-workspace\\gpt-pilot\\workspace\\vediolingo-web\\YouTube_Videos'):
    os.makedirs(save_path, exist_ok=True)

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best' if resolution == 'best' else f'bestvideo[height<={resolution}]+bestaudio/best[height<={resolution}]',
        'outtmpl': f'{save_path}/%(title)s/%(title)s.%(ext)s',  # 在以视频名称命名的文件夹中保存视频文件
        'noplaylist': True,
        'dateafter': start_date.strftime('%Y%m%d'),
        'writethumbnail': True,
        'postprocessors': [{
            'key': 'FFmpegThumbnailsConvertor',
            'format': 'jpg',
        },
        ],
        'retries': 5,
        'socket_timeout': 60,
    }

    with YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([channel_url])
        except Exception as e:
            print(f"Error downloading videos: {str(e)}")
            return

    # Organize thumbnails into folders named after the video titles
    for root, dirs, files in os.walk(save_path):
        for file in files:
            if file.endswith('.jpg'):
                video_name = os.path.splitext(file)[0]
                video_folder = os.path.join(save_path, video_name)
                if not os.path.exists(video_folder):
                    os.makedirs(video_folder)
                os.rename(os.path.join(root, file), os.path.join(video_folder, file))

    print(f"Download complete. Videos saved in {save_path}")

if __name__ == '__main__':
    channel_url = input('Please enter the URL of the YouTube channel: ')
    start_date_str = input('Please enter the start date (YYYY-MM-DD): ')
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    resolution = input(f'Please enter the desired resolution (360/720/1080/best, default {YTB_RESOLUTION}): ')
    resolution = resolution if resolution else YTB_RESOLUTION
    
    download_videos_from_channel(channel_url, start_date, resolution)