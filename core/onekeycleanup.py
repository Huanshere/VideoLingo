import os
import glob
import shutil

def cleanup():
    # Get video file name
    video_files = glob.glob("*.mp4") + glob.glob("*.webm")
    if not video_files:
        print("🚫 No video files found")
        return
    
    video_file = video_files[0]
    video_name = os.path.splitext(video_file)[0]

    # Create required folders
    os.makedirs("history", exist_ok=True)
    history_dir = os.path.join("history", video_name)
    log_dir = os.path.join(history_dir, "log")
    gpt_log_dir = os.path.join(history_dir, "gpt_log")

    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(gpt_log_dir, exist_ok=True)

    # Move log files
    for file in glob.glob("output/log/*"):
        move_file(file, log_dir)

    # Move gpt_log files
    for file in glob.glob("output/gpt_log/*"):
        move_file(file, gpt_log_dir)

    # Move subtitle files
    for file in glob.glob("output/*"):
        move_file(file, history_dir)

    # Move video files
    move_file(video_file, history_dir)

def move_file(src, dst):
    try:
        shutil.move(src, dst, copy_function=shutil.copy2)
        print(f"✅ 已移动: {src} -> {dst}")
    except shutil.Error as e:
        # 如果目标文件已存在，强制覆盖
        os.remove(dst)
        shutil.move(src, dst, copy_function=shutil.copy2)
        print(f"✅ 已覆盖并移动: {src} -> {dst}")

if __name__ == "__main__":
    cleanup()