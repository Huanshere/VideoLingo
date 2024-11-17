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
    
    console.print(Panel.fit("🚀 Starting Installation", style="bold magenta"))

    # Configure mirrors
    from core.pypi_autochoose import main as choose_mirror
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
        # requires both conda-ffmpeg and ffmpeg.exe
        console.print(Panel("📦 Installing ffmpeg through conda...", style="cyan"))
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
            print(f"{ffmpeg_exe} already exists")
            return

        console.print(Panel("📦 Downloading FFmpeg...", style="cyan"))
        response = requests.get(url)
        if response.status_code == 200:
            filename = "ffmpeg.zip" if system in ["Windows", "Darwin"] else "ffmpeg.tar.xz"
            with open(filename, 'wb') as f:
                f.write(response.content)
            console.print(Panel(f"FFmpeg downloaded: {filename}", style="cyan"))
        
            console.print(Panel("📦 Extracting FFmpeg...", style="cyan"))
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
            
            console.print(Panel("📦 Cleaning up...", style="cyan"))
            os.remove(filename)
            if system == "Windows":
                for item in os.listdir():
                    if os.path.isdir(item) and "ffmpeg" in item.lower():
                        shutil.rmtree(item)
            console.print(Panel("FFmpeg extraction completed", style="cyan"))
        else:
            console.print(Panel("❌ Failed to download FFmpeg", style="red"))

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
