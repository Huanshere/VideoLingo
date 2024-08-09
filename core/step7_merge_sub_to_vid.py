import os, glob, subprocess, time

EN_FONT_SIZE = 16
TRANS_FONT_SIZE = 18
FONT_NAME = 'Arial'
TRANS_FONT_NAME = 'Arial'
EN_FONT_COLOR = '&HFFFFFF' 
EN_OUTLINE_COLOR = '&H000000'
EN_OUTLINE_WIDTH = 1
EN_SHADOW_COLOR = '&H80000000'
TRANS_FONT_COLOR = '&H00FFFF'
TRANS_OUTLINE_COLOR = '&H000000'
TRANS_OUTLINE_WIDTH = 1 
TRANS_BACK_COLOR = '&H33000000'

TARGET_WIDTH = 854
TARGET_HEIGHT = 480 # for demo only 480p


def merge_subtitles_to_video():
    ## merge subtitles to video and save the output video
    video_files = glob.glob("*.mp4") + glob.glob("*.webm")
    if not video_files:
        print("No video files found in the current directory.")
        exit(1)
    video_file = video_files[0]
    en_srt = "output/english_subtitles.srt"
    trans_srt = "output/translated_subtitles.srt"

    if not os.path.exists(en_srt) or not os.path.exists(trans_srt):
        print("Subtitle files not found in the 'output' directory.")
        exit(1)

    output_video = "output/output_video_with_subs.mp4"
    os.makedirs(os.path.dirname(output_video), exist_ok=True)

    ffmpeg_cmd = [
        'ffmpeg', '-i', video_file,
        '-vf', (
            f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2,"
            f"subtitles={en_srt}:force_style='FontSize={EN_FONT_SIZE},FontName={FONT_NAME}," 
            f"PrimaryColour={EN_FONT_COLOR},OutlineColour={EN_OUTLINE_COLOR},OutlineWidth={EN_OUTLINE_WIDTH},"
            f"ShadowColour={EN_SHADOW_COLOR},BorderStyle=1',"
            f"subtitles={trans_srt}:force_style='FontSize={TRANS_FONT_SIZE},FontName={TRANS_FONT_NAME},"
            f"PrimaryColour={TRANS_FONT_COLOR},OutlineColour={TRANS_OUTLINE_COLOR},OutlineWidth={TRANS_OUTLINE_WIDTH},"
            f"BackColour={TRANS_BACK_COLOR},Alignment=2,MarginV=25,BorderStyle=4'"
        ),
        '-preset', 'veryfast', 
        '-y',
        output_video
    ]

    print("Starting FFmpeg process... should take less than 10s for 2mins video.")
    start_time = time.time()
    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        stdout, stderr = process.communicate(timeout=120)
        if process.returncode == 0:
            print(f"Process completed in {time.time() - start_time:.2f} seconds.")
            print("🎉🎥 `output_video_with_subs.mp4` generated successfully! Go check it out inside `output` 👀")
        else:
            print("Error occurred during FFmpeg execution:")
            print(stderr.decode())
    except subprocess.TimeoutExpired:
        process.kill()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        if process.poll() is None:
            process.kill()
    
if __name__ == "__main__":
    merge_subtitles_to_video()