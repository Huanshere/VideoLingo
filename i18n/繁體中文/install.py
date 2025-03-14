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
            print(f"檢測到 NVIDIA GPU")
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(handle)
                print(f"GPU {i}: {name}")
            return True
        else:
            print("未檢測到 NVIDIA GPU")
            return False
    except pynvml.NVMLError:
        print("未檢測到 NVIDIA GPU 或 NVIDIA 驅動未正確安裝")
        return False
    finally:
        pynvml.nvmlShutdown()

def check_ffmpeg():
    from rich.console import Console
    from rich.panel import Panel
    console = Console()
    
    try:
        # 檢查 ffmpeg 是否已安裝
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        console.print(Panel("✅ 已安裝 FFmpeg", style="green"))
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        system = platform.system()
        install_cmd = ""
        
        if system == "Windows":
            install_cmd = "choco install ffmpeg"
            extra_note = "請先安裝 Chocolatey (https://chocolatey.org/)"
        elif system == "Darwin":
            install_cmd = "brew install ffmpeg"
            extra_note = "請先安裝 Homebrew (https://brew.sh/)"
        elif system == "Linux":
            install_cmd = "sudo apt install ffmpeg  # Ubuntu/Debian\nsudo yum install ffmpeg  # CentOS/RHEL"
            extra_note = "請使用您的 Linux 發行版對應的包管理器"
        
        console.print(Panel.fit(
            f"❌ 未檢測到 FFmpeg\n\n"
            f"🛠️ 請使用以下命令安裝：\n[bold cyan]{install_cmd}[/bold cyan]\n\n"
            f"💡 注意：{extra_note}\n\n"
            f"🔄 安裝 FFmpeg 後，請重新運行安裝程序：[bold cyan]python install.py[/bold cyan]",
            style="red"
        ))
        raise SystemExit("需要安裝 FFmpeg。請安裝後重新運行安裝程序。")

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
    
    console.print(Panel.fit("🚀 開始安裝", style="bold magenta"))

    # 配置鏡像源
    from core.pypi_autochoose import main as choose_mirror
    choose_mirror()

    # 檢測系統和GPU
    has_gpu = platform.system() != 'Darwin' and check_nvidia_gpu()
    if has_gpu:
        console.print(Panel("🎮 檢測到 NVIDIA GPU，正在安裝 CUDA 版本的 PyTorch...", style="cyan"))
        subprocess.check_call([sys.executable, "-m", "pip", "install", "torch==2.0.0", "torchaudio==2.0.0", "--index-url", "https://download.pytorch.org/whl/cu118"])
    else:
        system_name = "🍎 MacOS" if platform.system() == 'Darwin' else "💻 未檢測到 NVIDIA GPU"
        console.print(Panel(f"{system_name}，正在安裝 CPU 版本的 PyTorch... 但轉寫速度會慢很多", style="cyan"))
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
            console.print(Panel(f"❌ 安裝依賴失敗: {str(e)}", style="red"))

    def install_ffmpeg():
        console.print(Panel("📦 正在通過 conda 安裝 ffmpeg...", style="cyan"))
        try:
            subprocess.check_call(["conda", "install", "-y", "ffmpeg"], shell=True)
            console.print(Panel("✅ FFmpeg 安裝完成", style="green"))
        except subprocess.CalledProcessError:
            console.print(Panel("❌ 通過 conda 安裝 FFmpeg 失敗", style="red"))

    def install_noto_font():
        # 檢測 Linux 發行版類型
        if os.path.exists('/etc/debian_version'):
            # Debian/Ubuntu 系統
            cmd = ['sudo', 'apt-get', 'install', '-y', 'fonts-noto']
            pkg_manager = "apt-get"
        elif os.path.exists('/etc/redhat-release'):
            # RHEL/CentOS/Fedora 系統
            cmd = ['sudo', 'yum', 'install', '-y', 'google-noto*']
            pkg_manager = "yum"
        else:
            console.print("⚠️ 無法識別的 Linux 發行版，請手動安裝 Noto 字體", style="yellow")
            return
            
        try:
            subprocess.run(cmd, check=True)
            console.print(f"✅ 使用 {pkg_manager} 成功安裝 Noto 字體", style="green")
        except subprocess.CalledProcessError:
            console.print("❌ 安裝 Noto 字體失敗，請手動安裝", style="red")

    if platform.system() == 'Linux':
        install_noto_font()

    install_requirements()
    check_ffmpeg()
    
    console.print(Panel.fit("安裝完成", style="bold green"))
    console.print("要啟動應用程序，請運行：")
    console.print("[bold cyan]streamlit run st.py[/bold cyan]")
    console.print("[yellow]注意：首次啟動可能需要1分鐘[/yellow]")
    
    # 添加故障排除提示
    console.print("\n[yellow]如果應用程序啟動失敗:[/yellow]")
    console.print("1. [yellow]檢查網絡連接[/yellow]")
    console.print("2. [yellow]重新運行安裝程序: [bold]python install.py[/bold][/yellow]")

    # 啟動應用程序
    subprocess.Popen(["streamlit", "run", "st.py"])

if __name__ == "__main__":
    main()
