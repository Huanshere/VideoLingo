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

def check_nvidia_gpu():
    install_package("pynvml")
    import pynvml
    try:
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()
        if device_count > 0:
            print(f"检测到 NVIDIA GPU")
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(handle)
                print(f"GPU {i}: {name}")
            return True
        else:
            print("未检测到 NVIDIA GPU")
            return False
    except pynvml.NVMLError:
        print("未检测到 NVIDIA GPU 或 NVIDIA 驱动未正确安装")
        return False
    finally:
        pynvml.nvmlShutdown()

def check_ffmpeg():
    from rich.console import Console
    from rich.panel import Panel
    console = Console()
    
    try:
        # 检查 ffmpeg 是否已安装
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        console.print(Panel("✅ 已安装 FFmpeg", style="green"))
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        system = platform.system()
        install_cmd = ""
        
        if system == "Windows":
            install_cmd = "choco install ffmpeg"
            extra_note = "请先安装 Chocolatey (https://chocolatey.org/)"
        elif system == "Darwin":
            install_cmd = "brew install ffmpeg"
            extra_note = "请先安装 Homebrew (https://brew.sh/)"
        elif system == "Linux":
            install_cmd = "sudo apt install ffmpeg  # Ubuntu/Debian\nsudo yum install ffmpeg  # CentOS/RHEL"
            extra_note = "请使用您的 Linux 发行版对应的包管理器"
        
        console.print(Panel.fit(
            f"❌ 未检测到 FFmpeg\n\n"
            f"🛠️ 请使用以下命令安装：\n[bold cyan]{install_cmd}[/bold cyan]\n\n"
            f"💡 注意：{extra_note}\n\n"
            f"🔄 安装 FFmpeg 后，请重新运行安装程序：[bold cyan]python install.py[/bold cyan]",
            style="red"
        ))
        raise SystemExit("需要安装 FFmpeg。请安装后重新运行安装程序。")

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
    has_gpu = platform.system() != 'Darwin' and check_nvidia_gpu()
    if has_gpu:
        console.print(Panel("🎮 检测到 NVIDIA GPU，正在安装 CUDA 版本的 PyTorch...", style="cyan"))
        subprocess.check_call([sys.executable, "-m", "pip", "install", "torch==2.0.0", "torchaudio==2.0.0", "--index-url", "https://download.pytorch.org/whl/cu118"])
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
    check_ffmpeg()
    
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
