from yt_dlp import YoutubeDL
import os

def download_video_ytdlp(url, save_path='./', progress_callback=None):
    ydl_opts = {
        'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    }
    
    if progress_callback:
        def progress_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes')
                downloaded = d.get('downloaded_bytes')
                if total and downloaded:
                    progress_callback(downloaded / total)
        
        ydl_opts['progress_hooks'] = [progress_hook]

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
    
    return filename

if __name__ == '__main__':
    # 示例用法
    url = input('请输入您想下载的视频URL: ')
    download_video_ytdlp(url)

