import os
import platform
import subprocess
import sys
import zipfile
import shutil

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def install_package(*packages):
    subprocess.check_call([sys.executable, "-m", "pip", "install", *packages])

install_package("requests", "rich", "ruamel.yaml")
from pypi_autochoose import main as choose_mirror

def check_gpu():
    """Check if NVIDIA GPU is available"""
    try:
        # 🔍 Try running nvidia-smi command to detect GPU
        subprocess.run(['nvidia-smi'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def main():
    from rich.console import Console
    from rich.panel import Panel
    
    console = Console()
    console.print(Panel.fit("🚀 Starting Installation", style="bold magenta"))

    # Configure mirrors
    console.print(Panel("⚙️ Configuring mirrors", style="bold yellow"))
    choose_mirror()

    # Detect system and GPU
    if platform.system() == 'Darwin':
        console.print(Panel("🍎 MacOS detected, installing CPU version of PyTorch... However, it would be extremely slow for transcription.", style="cyan"))
        subprocess.check_call([sys.executable, "-m", "pip", "install", "torch==2.1.2", "torchaudio==2.1.2"])
    else:
        has_gpu = check_gpu()
        if has_gpu:
            console.print(Panel("🎮 NVIDIA GPU detected, installing CUDA version of PyTorch...", style="cyan"))
            subprocess.check_call([sys.executable, "-m", "pip", "install", "torch==2.0.0", "torchaudio==2.0.0", "--index-url", "https://download.pytorch.org/whl/cu118"])
        else:
            console.print(Panel("💻 No NVIDIA GPU detected, installing CPU version of PyTorch... However, it would be extremely slow for transcription.", style="cyan"))
            subprocess.check_call([sys.executable, "-m", "pip", "install", "torch==2.1.2", "torchaudio==2.1.2"])
    
    # Install WhisperX
    console.print(Panel("📦 Installing WhisperX...", style="cyan"))
    current_dir = os.getcwd()
    whisperx_dir = os.path.join(current_dir, "third_party", "whisperX")
    os.chdir(whisperx_dir)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])
    os.chdir(current_dir)

    def install_requirements():
        try:
            with open("requirements.txt", "r", encoding="utf-8") as file:
                content = file.read()
            with open("requirements.txt", "w", encoding="gbk") as file:
                file.write(content)
        except Exception as e:
            print(f"Error converting requirements.txt: {str(e)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    def download_and_extract_ffmpeg():
        # 使用conda安装ffmpeg，这是因为pydub似乎还需要依赖于conda的ffmpeg
        try:
            subprocess.check_call(["conda", "install", "-y", "ffmpeg"])
            print("成功通过conda安装ffmpeg")
        except Exception as e:
            print(f"通过conda安装ffmpeg失败: {str(e)}")
        import requests
        system = platform.system()
        if system == "Windows":
            ffmpeg_exe = "ffmpeg.exe"
            url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        elif system == "Darwin":
            ffmpeg_exe = "ffmpeg"
            url = "https://evermeet.cx/ffmpeg/getrelease/zip"
        elif system == "Linux":
            ffmpeg_exe = "ffmpeg"
            url = "https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz"
        else:
            return

        if os.path.exists(ffmpeg_exe):
            print(f"{ffmpeg_exe} already exists")
            return

        print("Downloading FFmpeg")
        response = requests.get(url)
        if response.status_code == 200:
            filename = "ffmpeg.zip" if system in ["Windows", "Darwin"] else "ffmpeg.tar.xz"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"FFmpeg downloaded: {filename}")
        
            print("Extracting FFmpeg")
            if system == "Linux":
                import tarfile
                with tarfile.open(filename) as tar_ref:
                    for member in tar_ref.getmembers():
                        if member.name.endswith("ffmpeg"):
                            member.name = os.path.basename(member.name)
                            tar_ref.extract(member)
            else:
                with zipfile.ZipFile(filename, 'r') as zip_ref:
                    for file in zip_ref.namelist():
                        if file.endswith(ffmpeg_exe):
                            zip_ref.extract(file)
                            shutil.move(os.path.join(*file.split('/')[:-1], os.path.basename(file)), os.path.basename(file))
            
            print("Cleaning up")
            os.remove(filename)
            if system == "Windows":
                for item in os.listdir():
                    if os.path.isdir(item) and "ffmpeg" in item.lower():
                        shutil.rmtree(item)
            print("FFmpeg extraction completed")
        else:
            print("Failed to download FFmpeg")

    def install_noto_font():
        if platform.system() == 'Linux':
            try:
                # Try apt-get first (Debian-based systems)
                subprocess.run(['sudo', 'apt-get', 'install', '-y', 'fonts-noto'], check=True)
                print("Noto fonts installed successfully using apt-get.")
            except subprocess.CalledProcessError:
                try:
                    # If apt-get fails, try yum (RPM-based systems)
                    subprocess.run(['sudo', 'yum', 'install', '-y', 'fonts-noto'], check=True)
                    print("Noto fonts installed successfully using yum.")
                except subprocess.CalledProcessError:
                    print("Failed to install Noto fonts automatically. Please install them manually.")

    install_noto_font()
    install_requirements()
    download_and_extract_ffmpeg()
    
    console.print(Panel.fit("Installation completed", style="bold green"))
    console.print("To start the application, run:")
    console.print("[bold cyan]streamlit run st.py[/bold cyan]")

if __name__ == "__main__":
    main()
