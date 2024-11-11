import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import glob
import re
import subprocess
from core.config_utils import load_key

def sanitize_filename(filename):
    # Remove or replace illegal characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Ensure filename doesn't start or end with a dot or space
    filename = filename.strip('. ')
    # Use default name if filename is empty
    return filename if filename else 'video'

def download_video_ytdlp(url, save_path='output', resolution='1080', cutoff_time=None):
    allowed_resolutions = ['360', '1080', 'best']
    if resolution not in allowed_resolutions:
        resolution = '360'
    
    os.makedirs(save_path, exist_ok=True)
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best' if resolution == 'best' else f'bestvideo[height<={resolution}]+bestaudio/best[height<={resolution}]',
        'outtmpl': f'{save_path}/%(title)s.%(ext)s',
        'noplaylist': True,
        'writethumbnail': True,
        'postprocessors': [{
            'key': 'FFmpegThumbnailsConvertor',
            'format': 'jpg',
        }],
    }

    # Update yt-dlp to avoid download failure due to API changes
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to update yt-dlp: {e}")
    # Reload yt-dlp
    if 'yt_dlp' in sys.modules:
        del sys.modules['yt_dlp']
    from yt_dlp import YoutubeDL
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    # Check and rename files after download
    for file in os.listdir(save_path):
        if os.path.isfile(os.path.join(save_path, file)):
            filename, ext = os.path.splitext(file)
            new_filename = sanitize_filename(filename)
            if new_filename != filename:
                os.rename(os.path.join(save_path, file), os.path.join(save_path, new_filename + ext))

    # cut the video to make demo
    if cutoff_time:
        print(f"Cutoff time: {cutoff_time}, Now checking video duration...")
        video_file = find_video_files(save_path)
        
        # Use librosa to get video duration
        import librosa
        duration = librosa.get_duration(filename=video_file)
        
        if duration > cutoff_time:
            print(f"Video duration ({duration:.2f}s) is longer than cutoff time. Cutting the video...")
            file_name, file_extension = os.path.splitext(video_file)
            trimmed_file = f"{file_name}_trim{file_extension}"
            ffmpeg_cmd = ['ffmpeg', '-i', video_file, '-t', str(cutoff_time), '-c', 'copy', trimmed_file]
            print("🎬 Start cutting video...")
            process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding='utf-8')
            for line in process.stdout:
                print(line, end='')
            process.wait()
            print(f"✅ Video has been cut to the first {cutoff_time} seconds")
            
            # Remove the original file and rename the trimmed file
            os.remove(video_file)
            os.rename(trimmed_file, video_file)
            print(f"Original file removed and trimmed file renamed to {os.path.basename(video_file)}")
        else:
            print(f"Video duration ({duration:.2f}s) is not longer than cutoff time. No need to cut.")

def find_video_files(save_path='output'):
    video_files = [file for file in glob.glob(save_path + "/*") if os.path.splitext(file)[1][1:].lower() in load_key("allowed_video_formats")]
    # change \\ to /, this happen on windows
    if sys.platform.startswith('win'):
        video_files = [file.replace("\\", "/") for file in video_files]
    video_files = [file for file in video_files if not file.startswith("output/output")]
    # if num != 1, raise ValueError
    if len(video_files) != 1:
        raise ValueError(f"Number of videos found is not unique. Please check. Number of videos found: {len(video_files)}")
    return video_files[0]

if __name__ == '__main__':
    # Example usage
    url = input('Please enter the URL of the video you want to download: ')
    resolution = input('Please enter the desired resolution (360/1080, default 1080): ')
    resolution = int(resolution) if resolution.isdigit() else 1080
    download_video_ytdlp(url, resolution=resolution)
    print(f"🎥 Video has been downloaded to {find_video_files()}")
