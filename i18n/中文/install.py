import os
import platform
import subprocess
import sys
import zipfile
import shutil
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

ascii_logo = """
__     ___     _            _     _                    
\ \   / (_) __| | ___  ___ | |   (_)_ __   __ _  ___  
 \ \ / /| |/ _` |/ _ \/ _ \| |   | | '_ \ / _` |/ _ \ 
  \ V / | | (_| |  __/ (_) | |___| | | | | (_| | (_) |
   \_/  |_|\__,_|\___|\___/|_____|_|_| |_|\__, |\___/ 
                                          |___/        
"""

def install_package(*packages):
    subprocess.check_call([sys.executable, "-m", "pip", "install", *packages])

def check_gpu():
    try:
        subprocess.run(['nvidia-smi'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def main():
    install_package("requests", "rich", "ruamel.yaml")
    from rich.console import Console
    from rich.panel import Panel
    from rich.box import DOUBLE
    console = Console()
    
    width = max(len(line) for line in ascii_logo.splitlines()) + 4
    welcome_panel = Panel(
        ascii_logo,
        width=width,
        box=DOUBLE,
        title="[bold green]🌏[/bold green]",
        border_style="bright_blue"
    )
    console.print(welcome_panel)
    
    console.print(Panel.fit("🚀 开始安装", style="bold magenta"))

    # 配置镜像源
    from core.pypi_autochoose import main as choose_mirror
    choose_mirror()

    # 检测系统和GPU
    if platform.system() == 'Darwin':
        console.print(Panel("🍎 检测到 MacOS，正在安装 CPU 版本的 PyTorch... 但转写速度会慢很多", style="cyan"))
        subprocess.check_call([sys.executable, "-m", "pip", "install", "torch==2.1.2", "torchaudio==2.1.2"])
    else:
        has_gpu = check_gpu()
        if has_gpu:
            console.print(Panel("🎮 检测到 NVIDIA GPU，正在安装 CUDA 版本的 PyTorch...", style="cyan"))
            subprocess.check_call([sys.executable, "-m", "pip", "install", "torch==2.0.0", "torchaudio==2.0.0", "--index-url", "https://download.pytorch.org/whl/cu118"])
        else:
            console.print(Panel("💻 未检测到 NVIDIA GPU，正在安装 CPU 版本的 PyTorch... 但转写速度会慢很多", style="cyan"))
            subprocess.check_call([sys.executable, "-m", "pip", "install", "torch==2.1.2", "torchaudio==2.1.2"])
    
    # 安装 WhisperX
    console.print(Panel("📦 正在安装 WhisperX...", style="cyan"))
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
            print(f"转换 requirements.txt 时出错: {str(e)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    def download_and_extract_ffmpeg():
        # VL requires both conda/system ffmpeg and ffmpeg.exe...
        system = platform.system()
        if system == "Linux":
            # Linux: use apt or yum to install ffmpeg
            try:
                console.print(Panel("📦 正在通过 apt 安装 ffmpeg...", style="cyan"))
                subprocess.check_call(["sudo", "apt", "install", "-y", "ffmpeg"])
            except subprocess.CalledProcessError:
                try:
                    console.print(Panel("📦 正在通过 yum 安装 ffmpeg...", style="cyan"))
                    subprocess.check_call(["sudo", "yum", "install", "-y", "ffmpeg"], shell=True)
                except subprocess.CalledProcessError:
                    console.print(Panel("❌ 通过包管理器安装 ffmpeg 失败", style="red"))
        else:
            # Windows/MacOS: use conda to install ffmpeg
            console.print(Panel("📦 正在通过 conda 安装 ffmpeg...", style="cyan"))
            subprocess.check_call(["conda", "install", "-y", "ffmpeg"], shell=True)

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
            print(f"{ffmpeg_exe} 已存在")
            return

        console.print(Panel("📦 正在下载 FFmpeg...", style="cyan"))
        response = requests.get(url)
        if response.status_code == 200:
            filename = "ffmpeg.zip" if system in ["Windows", "Darwin"] else "ffmpeg.tar.xz"
            with open(filename, 'wb') as f:
                f.write(response.content)
            console.print(Panel(f"FFmpeg 下载完成: {filename}", style="cyan"))
        
            console.print(Panel("📦 正在解压 FFmpeg...", style="cyan"))
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
            
            console.print(Panel("📦 正在清理...", style="cyan"))
            os.remove(filename)
            if system == "Windows":
                for item in os.listdir():
                    if os.path.isdir(item) and "ffmpeg" in item.lower():
                        shutil.rmtree(item)
            console.print(Panel("FFmpeg 解压完成", style="cyan"))
        else:
            console.print(Panel("❌ FFmpeg 下载失败", style="red"))

    def install_noto_font():
        if platform.system() == 'Linux':
            try:
                # 首先尝试 apt-get (基于 Debian 的系统)
                subprocess.run(['sudo', 'apt-get', 'install', '-y', 'fonts-noto'], check=True)
                print("使用 apt-get 成功安装了 Noto 字体。")
            except subprocess.CalledProcessError:
                try:
                    # 如果 apt-get 失败，尝试 yum (基于 RPM 的系统)
                    subprocess.run(['sudo', 'yum', 'install', '-y', 'fonts-noto'], check=True)
                    print("使用 yum 成功安装了 Noto 字体。")
                except subprocess.CalledProcessError:
                    print("自动安装 Noto 字体失败。请手动安装。")

    install_noto_font()
    install_requirements()
    download_and_extract_ffmpeg()
    
    console.print(Panel.fit("安装完成", style="bold green"))
    console.print("要启动应用程序，请运行：")
    console.print("[bold cyan]streamlit run st.py[/bold cyan]")

if __name__ == "__main__":
    main()
