import os
import platform
import subprocess
import sys
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

def install_ffmpeg():
    from rich.console import Console
    from rich.panel import Panel
    console = Console()
    
    system = platform.system()
    
    if system == "Linux":
        console.print(Panel("📦 正在安装 FFmpeg...", style="cyan"))
        try:
            subprocess.check_call(["sudo", "apt", "install", "-y", "ffmpeg"])
        except subprocess.CalledProcessError:
            try:
                subprocess.check_call(["sudo", "yum", "install", "-y", "ffmpeg"], shell=True)
            except subprocess.CalledProcessError:
                console.print(Panel("❌ 通过包管理器安装 FFmpeg 失败", style="red"))
    else:
        console.print(Panel("📦 正在安装 FFmpeg...", style="cyan"))
        download_and_extract_ffmpeg()

def download_and_extract_ffmpeg():
    import requests
    import zipfile
    import shutil
    from rich.console import Console
    from rich.panel import Panel
    console = Console()
    
    system = platform.system()
    if system == "Windows":
        ffmpeg_exe = "ffmpeg.exe"
        url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    elif system == "Darwin":
        ffmpeg_exe = "ffmpeg"
        url = "https://evermeet.cx/ffmpeg/getrelease/zip"
    else:
        console.print(Panel("❌ 不支持的系统，无法手动安装 FFmpeg", style="red"))
        return

    if os.path.exists(ffmpeg_exe):
        console.print(f"✅ {ffmpeg_exe} 已存在")
        return

    # 下载和解压逻辑
    console.print(Panel("📦 正在下载 FFmpeg...", style="cyan"))
    response = requests.get(url)
    if response.status_code == 200:
        filename = "ffmpeg.zip" if system in ["Windows", "Darwin"] else "ffmpeg.tar.xz"
        with open(filename, 'wb') as f:
            f.write(response.content)
        
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
        
        # 清理临时文件
        os.remove(filename)
        if system == "Windows":
            for item in os.listdir():
                if os.path.isdir(item) and "ffmpeg" in item.lower():
                    shutil.rmtree(item)
        console.print(Panel("✅ FFmpeg 安装完成", style="green"))
    else:
        console.print(Panel("❌ FFmpeg 下载失败", style="red"))

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
    has_gpu = platform.system() != 'Darwin' and check_gpu()
    if has_gpu:
        console.print(Panel("🎮 检测到 NVIDIA GPU，正在安装 CUDA 版本的 PyTorch...", style="cyan"))
        subprocess.check_call(["conda", "install", "-y", "pytorch==2.0.0", "torchaudio==2.0.0", "pytorch-cuda=11.8", "-c", "pytorch", "-c", "nvidia"])
    else:
        system_name = "🍎 MacOS" if platform.system() == 'Darwin' else "💻 未检测到 NVIDIA GPU"
        console.print(Panel(f"{system_name}，正在安装 CPU 版本的 PyTorch... 但转写速度会慢很多", style="cyan"))
        subprocess.check_call([sys.executable, "-m", "pip", "install", "torch==2.1.2", "torchaudio==2.1.2"])

    def install_requirements():
        try:
            subprocess.check_call([
                sys.executable, 
                "-m", 
                "pip", 
                "install", 
                "-r", 
                "requirements.txt"
            ], env={**os.environ, "PIP_NO_CACHE_DIR": "0", "PYTHONIOENCODING": "utf-8"})
        except subprocess.CalledProcessError as e:
            console.print(Panel(f"❌ 安装依赖失败: {str(e)}", style="red"))

    def install_ffmpeg():
        console.print(Panel("📦 正在通过 conda 安装 ffmpeg...", style="cyan"))
        try:
            subprocess.check_call(["conda", "install", "-y", "ffmpeg"], shell=True)
            console.print(Panel("✅ FFmpeg 安装完成", style="green"))
        except subprocess.CalledProcessError:
            console.print(Panel("❌ 通过 conda 安装 FFmpeg 失败", style="red"))

    def install_noto_font():
        # 检测 Linux 发行版类型
        if os.path.exists('/etc/debian_version'):
            # Debian/Ubuntu 系统
            cmd = ['sudo', 'apt-get', 'install', '-y', 'fonts-noto']
            pkg_manager = "apt-get"
        elif os.path.exists('/etc/redhat-release'):
            # RHEL/CentOS/Fedora 系统
            cmd = ['sudo', 'yum', 'install', '-y', 'google-noto*']
            pkg_manager = "yum"
        else:
            console.print("⚠️ 无法识别的 Linux 发行版，请手动安装 Noto 字体", style="yellow")
            return
            
        try:
            subprocess.run(cmd, check=True)
            console.print(f"✅ 使用 {pkg_manager} 成功安装 Noto 字体", style="green")
        except subprocess.CalledProcessError:
            console.print("❌ 安装 Noto 字体失败，请手动安装", style="red")

    if platform.system() == 'Linux':
        install_noto_font()

    install_requirements()
    install_ffmpeg()
    
    console.print(Panel.fit("安装完成", style="bold green"))
    console.print("要启动应用程序，请运行：")
    console.print("[bold cyan]streamlit run st.py[/bold cyan]")
    console.print("[yellow]注意：首次启动可能需要1分钟[/yellow]")
    
    # 添加故障排除提示
    console.print("\n[yellow]如果应用程序启动失败:[/yellow]")
    console.print("1. [yellow]检查网络连接[/yellow]")
    console.print("2. [yellow]重新运行安装程序: [bold]python install.py[/bold][/yellow]")

    # 启动应用程序
    subprocess.Popen(["streamlit", "run", "st.py"])

if __name__ == "__main__":
    main()
