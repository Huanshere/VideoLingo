import os
import platform
import subprocess
import sys
import zipfile
import shutil
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def install_package(*packages):
    subprocess.check_call([sys.executable, "-m", "pip", "install", *packages])

def install_requirements():
    """Install requirements from requirements.txt file."""
    if os.path.exists("requirements.txt"):
        print("正在将requirements.txt转换为GBK编码...")
        try:
            with open("requirements.txt", "r", encoding="utf-8") as file:
                content = file.read()
            with open("requirements.txt", "w", encoding="gbk") as file:
                file.write(content)
            print("转换完成。")
        except UnicodeDecodeError:
            print("requirements.txt已经是GBK编码，无需转换。")
        except Exception as e:
            print(f"转换编码时出错：{str(e)}")
        
        print("正在从requirements.txt安装依赖...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    else:
        print("未找到requirements.txt。跳过安装。")

def dowanload_uvr_model():
    """Download the specified uvr model."""
    if not os.path.exists("_model_cache/uvr5_weights/HP2_all_vocals.pth"):
        os.makedirs("_model_cache/uvr5_weights", exist_ok=True)
        import requests
        print("正在下载UVR模型...")
        url = "https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/e992cb1bc5d777fcddce20735a899219b1d46aba/uvr5_weights/HP2_all_vocals.pth"
        response = requests.get(url)
        with open("_model_cache/uvr5_weights/HP2_all_vocals.pth", "wb") as file:
            file.write(response.content)
        print("UVR模型下载成功。")
    else:
        print("HP2_all_vocals.pth已存在。跳过下载。")

def download_and_extract_ffmpeg():
    """Download FFmpeg based on the platform, extract it, and clean up."""
    system = platform.system()
    if system == "Windows":
        ffmpeg_exe = "ffmpeg.exe"
        url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    elif system == "Darwin":
        ffmpeg_exe = "ffmpeg"
        url = "https://evermeet.cx/ffmpeg/ffmpeg-4.4.zip"
    elif system == "Linux":
        ffmpeg_exe = "ffmpeg"
        url = "https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz"
    else:
        return

    if os.path.exists(ffmpeg_exe):
        print(f"{ffmpeg_exe}已存在。跳过下载。")
        return

    print("正在下载FFmpeg...")
    import requests
    response = requests.get(url)
    if response.status_code == 200:
        filename = "ffmpeg.zip"
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"FFmpeg已下载到{filename}")
        
        print("正在解压FFmpeg...")
        if system == "Linux":
            import tarfile
            with tarfile.open(filename) as tar_ref:
                for member in tar_ref.getmembers():
                    if member.name.endswith("ffmpeg"):
                        member.name = os.path.basename(member.name)
                        tar_ref.extract(member)
                        break
        else:
            with zipfile.ZipFile(filename, 'r') as zip_ref:
                for file in zip_ref.namelist():
                    if file.endswith(ffmpeg_exe):
                        zip_ref.extract(file)
                        shutil.move(os.path.join(*file.split('/')[:-1], ffmpeg_exe), ffmpeg_exe)
                        break
        
        print("正在清理...")
        os.remove(filename)  
        if system != "Linux":
            for item in os.listdir():
                if os.path.isdir(item) and "ffmpeg" in item.lower():
                    shutil.rmtree(item)
        print("FFmpeg解压完成。")
    else:
        print("下载FFmpeg失败")

def init_config():
    """Initialize the config.py file with the specified API key and base URL."""
    if not os.path.exists("config.py"):
        # 从 config.example.py 复制 config.py
        shutil.copy("config.example.py", "config.py")
        print("config.py文件已创建。请在config.py文件中填写API密钥和基础URL。") 
    else:
        print("config.py文件已存在。")

def install_whisper_model(choice):
    if choice == '1':
        print("正在安装 whisper_timestamped...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "whisper-timestamped"])
    elif choice == '2':
        print("正在安装 whisperX...")
        current_dir = os.getcwd()
        whisperx_dir = os.path.join(current_dir, "third_party", "whisperX")
        os.chdir(whisperx_dir)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])
        os.chdir(current_dir)

def main():
    print("开始安装...")

    # 初始化 config.py 文件
    init_config()

    # 安装 requests
    install_package("requests")
    
    # 用户选择 Whisper 模型
    print("\n请选择要安装的 Whisper 模型：")
    print("1. whisper_timestamped")
    print("2. whisperX")
    print("3. whisperX_api")
    choice = input("请输入选项编号 (1, 2 或 3): ")
    
    # 安装 PyTorch
    if choice in ['1', '2']:
        print("正在安装支持 CUDA 的 PyTorch...")
        subprocess.check_call(["conda", "install", "pytorch==2.0.0", "torchaudio==2.0.0", "pytorch-cuda=11.8", "-c", "pytorch", "-c", "nvidia", "-y"])
    elif choice == '3':
        print("正在安装 cpu 版本的 PyTorch...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "torch", "torchaudio"])
    
    # 安装其他依赖
    install_requirements()

    # 安装选择的 Whisper 模型
    install_whisper_model(choice)

    # 下载并解压 FFmpeg
    download_and_extract_ffmpeg()
    
    print("所有安装步骤都完成啦!")
    print("请使用以下命令启动 Streamlit：")
    print("streamlit run st.py")

if __name__ == "__main__":
    main()