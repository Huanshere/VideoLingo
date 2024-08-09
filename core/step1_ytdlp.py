from yt_dlp import YoutubeDL

def download_video_ytdlp(url, save_path='./'):
    ydl_opts = {
        'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
        'outtmpl': f'{save_path}/%(title)s.%(ext)s'
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


if __name__ == '__main__':
    # example usage
    download_video_ytdlp('https://www.youtube.com/watch?v=_inKs4eeHiI&t=19s&pp=ygUNa3VuZ2Z1IHBhbmRhcw%3D%3D')
