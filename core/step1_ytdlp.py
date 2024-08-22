from yt_dlp import YoutubeDL

def download_video_ytdlp(url, save_path='./', resolution=1080):
    allowed_resolutions = [360, 480, 1080]
    if resolution not in allowed_resolutions:
        resolution = 1080
    
    ydl_opts = {
        'format': f'bestvideo[height<={resolution}]+bestaudio/best[height<={resolution}]',
        'outtmpl': f'{save_path}/%(title)s.%(ext)s'
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


if __name__ == '__main__':
    # 示例用法
    url = input('请输入您想下载的视频URL: ')
    resolution = input('请输入所需分辨率 (360/480/1080，默认1080): ')
    resolution = int(resolution) if resolution.isdigit() else 1080
    download_video_ytdlp(url, resolution=resolution)
