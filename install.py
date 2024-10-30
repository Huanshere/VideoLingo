import os
import platform
import subprocess
import sys
import zipfile
import shutil
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def install_package(*packages):
    subprocess.check_call([sys.executable, "-m", "pip", "install", *packages])

install_package("requests", "rich", "ruamel.yaml")
from pypi_autochoose import main as choose_mirror

def main():
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel

    console = Console()

    console.print(Panel.fit("Starting installation", style="bold magenta"))

    # Execute mirror configuration
    console.print(Panel("Configuring mirror", style="bold yellow"))
    choose_mirror()

    def install_requirements():
        try:
            with open("requirements.txt", "r", encoding="utf-8") as file:
                content = file.read()
            with open("requirements.txt", "w", encoding="gbk") as file:
                file.write(content)
        except Exception as e:
            print(f"Error converting requirements.txt: {str(e)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    def test_mirror_speed(name, base_url):
        import requests
        test_url = f"{base_url}lj1995/VoiceConversionWebUI/resolve/main/README.md"
        max_retries = 3
        timeout = 10

        for attempt in range(max_retries):
            try:
                start_time = time.time()
                response = requests.head(test_url, timeout=timeout)
                end_time = time.time()
                if response.status_code == 200:
                    speed = (end_time - start_time) * 1000 
                    return name, speed
            except requests.RequestException:
                if attempt == max_retries - 1:
                    return name, float('inf')
                time.sleep(1)  # Wait 1 second before retrying

        return name, float('inf')

    def download_and_extract_ffmpeg():
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

    # User selects Whisper model
    table = Table(title="Whisper Model Selection")
    table.add_column("Option", style="cyan", no_wrap=True)
    table.add_column("Model", style="magenta")
    table.add_column("Description", style="green")
    table.add_row("1", "whisperX 💻", "Local processing with whisperX")
    table.add_row("2", "whisperXapi ☁️", "Cloud processing with whisperXapi")
    console.print(table)

    console.print("WhisperX processes audio locally on your machine, while whisperXapi uses cloud processing.")

    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = console.input("Enter your choice (1 or 2): ")

    if platform.system() == 'Darwin':
        console.print(Panel("For MacOS, installing CPU version of PyTorch...", style="cyan"))
        subprocess.check_call([sys.executable, "-m", "pip", "install", "torch", "torchaudio"])
        if choice == '1':
            print("Installing whisperX...")
            current_dir = os.getcwd()
            whisperx_dir = os.path.join(current_dir, "third_party", "whisperX")
            os.chdir(whisperx_dir)
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])
            os.chdir(current_dir)
    else:
        if choice == '1':
            console.print(Panel("Installing PyTorch with CUDA support...", style="cyan"))
            subprocess.check_call([sys.executable, "-m", "pip", "install", "torch==2.0.0", "torchaudio==2.0.0", "--index-url", "https://download.pytorch.org/whl/cu118"])

            print("Installing whisperX...")
            current_dir = os.getcwd()
            whisperx_dir = os.path.join(current_dir, "third_party", "whisperX")
            os.chdir(whisperx_dir)
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])
            os.chdir(current_dir)
        elif choice == '2':
            table = Table(title="PyTorch Version Selection")
            table.add_column("Option", style="cyan", no_wrap=True)
            table.add_column("Model", style="magenta")
            table.add_column("Description", style="green")
            table.add_row("1", "CPU", "Choose this if you're using Mac, non-NVIDIA GPU, or don't need GPU acceleration")
            table.add_row("2", "GPU", "Significantly speeds up Demucs voice separation. Strongly recommended if you need dubbing functionality and have an NVIDIA GPU.")
            console.print(table)

            torch_choice = console.input("Please enter the option number (1 for CPU or 2 for GPU): ")
            if torch_choice == '1':
                console.print(Panel("Installing CPU version of PyTorch...", style="cyan"))
                subprocess.check_call([sys.executable, "-m", "pip", "install", "torch", "torchaudio"])
            elif torch_choice == '2':
                console.print(Panel("Installing GPU version of PyTorch with CUDA 11.8...", style="cyan"))
                subprocess.check_call([sys.executable, "-m", "pip", "install", "torch", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cu118"])
            else:
                console.print("Invalid choice. Defaulting to CPU version.")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "torch", "torchaudio"])
        else:
            raise ValueError("Invalid choice. Please enter 1 or 2. Try again.")

    install_noto_font()
    install_requirements()
    download_and_extract_ffmpeg()
    
    console.print(Panel.fit("Installation completed", style="bold green"))
    console.print("To start the application, run:")
    console.print("[bold cyan]streamlit run st.py[/bold cyan]")

if __name__ == "__main__":
    main()
