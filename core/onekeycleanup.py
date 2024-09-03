import os, sys
import glob
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.step1_ytdlp import find_video_files
import shutil

def cleanup():
    # Get video file name
    video_file = find_video_files()
    video_name = video_file.split("/")[1]
    video_name = os.path.splitext(video_name)[0]
    video_name = sanitize_filename(video_name)
    
    # Create required folders
    os.makedirs("history", exist_ok=True)
    history_dir = os.path.join("history", video_name)
    log_dir = os.path.join(history_dir, "log")
    gpt_log_dir = os.path.join(history_dir, "gpt_log")
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(gpt_log_dir, exist_ok=True)

    # 移动非日志文件
    for file in glob.glob("output/*"):
        if not file.endswith(('log', 'gpt_log')):
            move_file(file, history_dir)

    # 移动 log 文件
    for file in glob.glob("output/log/*"):
        move_file(file, log_dir)

    # 移动 gpt_log 文件
    for file in glob.glob("output/gpt_log/*"):
        move_file(file, gpt_log_dir)

    # 删除空的 output 目录
    try:
        os.rmdir("output/log")
        os.rmdir("output/gpt_log")
        os.rmdir("output")
    except OSError:
        pass  # 忽略删除失败的错误

def move_file(src, dst):
    try:
        # 获取源文件的文件名
        src_filename = os.path.basename(src)
        # 使用 os.path.join 来确保路径的正确性，并包含文件名
        dst = os.path.join(dst, sanitize_filename(src_filename))
        
        if os.path.exists(dst):
            if os.path.isdir(dst):
                # 如果目标是文件夹，尝试删除文件夹内容
                shutil.rmtree(dst, ignore_errors=True)
            else:
                # 如果目标是文件，尝试删除文件
                os.remove(dst)
        
        shutil.move(src, dst, copy_function=shutil.copy2)
        print(f"✅ 已移动: {src} -> {dst}")
    except PermissionError:
        print(f"⚠️ 权限错误: 无法删除 {dst}，尝试直接覆盖")
        try:
            shutil.copy2(src, dst)
            os.remove(src)
            print(f"✅ 已复制并删除源文件: {src} -> {dst}")
        except Exception as e:
            print(f"❌ 移动失败: {src} -> {dst}")
            print(f"错误信息: {str(e)}")
    except Exception as e:
        print(f"❌ 移动失败: {src} -> {dst}")
        print(f"错误信息: {str(e)}")

def sanitize_filename(filename):
    # 移除或替换不允许的字符
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

if __name__ == "__main__":
    cleanup()