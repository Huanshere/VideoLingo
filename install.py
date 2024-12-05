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
            print(f"Detected NVIDIA GPU(s)")
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(handle)
                print(f"GPU {i}: {name}")
            return True
        else:
            print("No NVIDIA GPU detected")
            return False
    except pynvml.NVMLError:
        print("No NVIDIA GPU detected or NVIDIA drivers not properly installed")
        return False
    finally:
        pynvml.nvmlShutdown()

def check_ffmpeg():
    from rich.console import Console
    from rich.panel import Panel
    console = Console()
    
    try:
        # Check if ffmpeg is installed
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        console.print(Panel("✅ FFmpeg is already installed", style="green"))
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        system = platform.system()
        install_cmd = ""
        
        if system == "Windows":
            install_cmd = "choco install ffmpeg"
            extra_note = "Install Chocolatey first (https://chocolatey.org/)"
        elif system == "Darwin":
            install_cmd = "brew install ffmpeg"
            extra_note = "Install Homebrew first (https://brew.sh/)"
        elif system == "Linux":
            install_cmd = "sudo apt install ffmpeg  # Ubuntu/Debian\nsudo yum install ffmpeg  # CentOS/RHEL"
            extra_note = "Use your distribution's package manager"
        
        console.print(Panel.fit(
            f"❌ FFmpeg not found\n\n"
            f"🛠️ Install using:\n[bold cyan]{install_cmd}[/bold cyan]\n\n"
            f"💡 Note: {extra_note}\n\n"
            f"🔄 After installing FFmpeg, please run this installer again: [bold cyan]python install.py[/bold cyan]",
            style="red"
        ))
        raise SystemExit("FFmpeg is required. Please install it and run the installer again.")

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
    
    console.print(Panel.fit("🚀 Starting Installation", style="bold magenta"))

    # Configure mirrors
    from core.pypi_autochoose import main as choose_mirror
    choose_mirror()

    # Detect system and GPU
    has_gpu = platform.system() != 'Darwin' and check_nvidia_gpu()
    if has_gpu:
        console.print(Panel("🎮 NVIDIA GPU detected, installing CUDA version of PyTorch...", style="cyan"))
        subprocess.check_call([sys.executable, "-m", "pip", "install", "torch==2.0.0", "torchaudio==2.0.0", "--index-url", "https://download.pytorch.org/whl/cu118"])
    else:
        system_name = "🍎 MacOS" if platform.system() == 'Darwin' else "💻 No NVIDIA GPU"
        console.print(Panel(f"{system_name} detected, installing CPU version of PyTorch... However, it would be extremely slow for transcription.", style="cyan"))
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
            console.print(Panel(f"❌ Failed to install requirements: {str(e)}", style="red"))

    def install_noto_font():
        # Detect Linux distribution type
        if os.path.exists('/etc/debian_version'):
            # Debian/Ubuntu systems
            cmd = ['sudo', 'apt-get', 'install', '-y', 'fonts-noto']
            pkg_manager = "apt-get"
        elif os.path.exists('/etc/redhat-release'):
            # RHEL/CentOS/Fedora systems
            cmd = ['sudo', 'yum', 'install', '-y', 'google-noto*']
            pkg_manager = "yum"
        else:
            console.print("⚠️ Unrecognized Linux distribution, please install Noto fonts manually", style="yellow")
            return
            
        try:
            subprocess.run(cmd, check=True)
            console.print(f"✅ Successfully installed Noto fonts using {pkg_manager}", style="green")
        except subprocess.CalledProcessError:
            console.print("❌ Failed to install Noto fonts, please install manually", style="red")

    if platform.system() == 'Linux':
        install_noto_font()
    
    install_requirements()
    check_ffmpeg()
    
    console.print(Panel.fit("Installation completed", style="bold green"))
    console.print("To start the application, run:")
    console.print("[bold cyan]streamlit run st.py[/bold cyan]")
    console.print("[yellow]Note: First startup may take up to 1 minute[/yellow]")
    
    # Add troubleshooting tips
    console.print("\n[yellow]If the application fails to start:[/yellow]")
    console.print("1. [yellow]Check your network connection[/yellow]")
    console.print("2. [yellow]Re-run the installer: [bold]python install.py[/bold][/yellow]")

    # start the application
    subprocess.Popen(["streamlit", "run", "st.py"])

if __name__ == "__main__":
    main()
