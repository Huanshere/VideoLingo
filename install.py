import os
import platform
import subprocess
import sys
import zipfile
import shutil
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def install_package(*packages):
    subprocess.check_call([sys.executable, "-m", "pip", "install", *packages])

def main():
    # Install rich first
    install_package("rich")

    # Now import rich components
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel

    console = Console()
    console.print(Panel.fit("Starting installation...", style="bold magenta"))

    def install_requirements():
        """Install requirements from requirements.txt file."""
        if os.path.exists("requirements.txt"):
            print("Converting requirements.txt to GBK encoding...")
            try:
                with open("requirements.txt", "r", encoding="utf-8") as file:
                    content = file.read()
                with open("requirements.txt", "w", encoding="gbk") as file:
                    file.write(content)
                print("Conversion completed.")
            except UnicodeDecodeError:
                print("requirements.txt is already in GBK encoding, no conversion needed.")
            except Exception as e:
                print(f"Error occurred during encoding conversion: {str(e)}")
            
            print("Installing dependencies from requirements.txt...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        else:
            print("requirements.txt not found. Skipping installation.")

    def dowanload_uvr_model():
        """Download the specified uvr model."""
        if not os.path.exists("_model_cache/uvr5_weights/HP2_all_vocals.pth"):
            os.makedirs("_model_cache/uvr5_weights", exist_ok=True)
            import requests
            print("Downloading UVR model...")
            url = "https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/e992cb1bc5d777fcddce20735a899219b1d46aba/uvr5_weights/HP2_all_vocals.pth"
            response = requests.get(url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            with open("_model_cache/uvr5_weights/HP2_all_vocals.pth", "wb") as file:
                for data in response.iter_content(chunk_size=4096):
                    size = file.write(data)
                    print(f"Downloaded: {(size/total_size)*100:.2f}%", end="\r")
            print("\nUVR model downloaded successfully.")
        else:
            print("HP2_all_vocals.pth already exists. Skipping download.")

    def download_and_extract_ffmpeg():
        """Download FFmpeg and FFprobe based on the platform, extract them, and clean up."""
        system = platform.system()
        if system == "Windows":
            ffmpeg_exe = "ffmpeg.exe"
            ffprobe_exe = "ffprobe.exe"
            url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        elif system == "Darwin":
            print("For macOS users, please install FFmpeg using Homebrew:\n"
                  "1. Install Homebrew if you haven't: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"\n"
                  "2. Then run: brew install ffmpeg")
            return
        elif system == "Linux":
            ffmpeg_exe = "ffmpeg"
            ffprobe_exe = "ffprobe"
            url = "https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz"
        else:
            return

        if os.path.exists(ffmpeg_exe) and os.path.exists(ffprobe_exe):
            print(f"{ffmpeg_exe} and {ffprobe_exe} already exist. Skipping download.")
            return

        print("Downloading FFmpeg and FFprobe...")
        import requests

        response = requests.get(url)
        if response.status_code == 200:
            filename = "ffmpeg.zip" if system == "Windows" else "ffmpeg.tar.xz"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"FFmpeg and FFprobe have been downloaded to {filename}")
        
            print("Extracting FFmpeg and FFprobe...")
            if system == "Linux":
                import tarfile
                with tarfile.open(filename) as tar_ref:
                    for member in tar_ref.getmembers():
                        if member.name.endswith(("ffmpeg", "ffprobe")):
                            member.name = os.path.basename(member.name)
                            tar_ref.extract(member)
            else:
                with zipfile.ZipFile(filename, 'r') as zip_ref:
                    for file in zip_ref.namelist():
                        if file.endswith((ffmpeg_exe, ffprobe_exe)):
                            zip_ref.extract(file)
                            shutil.move(os.path.join(*file.split('/')[:-1], os.path.basename(file)), os.path.basename(file))
            
            print("Cleaning up...")
            os.remove(filename)
            if system == "Windows":
                for item in os.listdir():
                    if os.path.isdir(item) and "ffmpeg" in item.lower():
                        shutil.rmtree(item)
            print("FFmpeg and FFprobe extraction completed.")
        else:
            print("Failed to download FFmpeg and FFprobe")

    def init_config():
        """Initialize the config.py file with the specified API key and base URL."""
        if not os.path.exists("config.py"):
            # Copy config.py from config.example.py
            shutil.copy("config.example.py", "config.py")
            print("config.py file has been created. Please fill in the API key and base URL in the config.py file.")
        else:
            print("config.py file already exists.")

    # Initialize config.py file
    init_config()

    # Install requests
    console.print(Panel("Installing requests...", style="cyan"))
    install_package("requests")
    
    # User selects Whisper model
    table = Table(title="Whisper Model Selection")
    table.add_column("Option", style="cyan", no_wrap=True)
    table.add_column("Model", style="magenta")
    table.add_column("Description", style="green")
    table.add_row("1", "whisperX 💻")
    table.add_row("2", "whisperXapi ☁️")
    console.print(table)

    console.print("If you're unsure about the differences between models, please see https://github.com/Huanshere/VideoLingo/")
    choice = console.input("Please enter the option number (1 or 2): ")

    # Install PyTorch and WhisperX
    if choice == '1':
        console.print(Panel("Installing PyTorch with CUDA support...", style="cyan"))
        subprocess.check_call(["conda", "install", "pytorch==2.0.0", "torchaudio==2.0.0", "pytorch-cuda=11.8", "-c", "pytorch", "-c", "nvidia", "-y"])
        
        print("Installing whisperX...")
        current_dir = os.getcwd()
        whisperx_dir = os.path.join(current_dir, "third_party", "whisperX")
        os.chdir(whisperx_dir)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])
        os.chdir(current_dir)
    elif choice == '2':
        table = Table(title="PyTorch Version Selection")
        table.add_column("Option", style="cyan", no_wrap=True)
        table.add_column("Version", style="magenta")
        table.add_column("Description", style="green")
        table.add_row("1", "CPU", "Choose this if you're using Mac, non-NVIDIA GPU, or don't need GPU acceleration")
        table.add_row("2", "GPU", "Significantly speeds up UVR5 voice separation. Strongly recommended if you need dubbing functionality and have an NVIDIA GPU.")
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
    # Install other dependencies
    install_requirements()

    # Download UVR model
    dowanload_uvr_model()
    
    # Download and extract FFmpeg
    download_and_extract_ffmpeg()
    
    console.print(Panel.fit("All installation steps are completed!", style="bold green"))
    console.print("Please use the following command to start Streamlit:")
    console.print("[bold cyan]streamlit run st.py[/bold cyan]")

if __name__ == "__main__":
    main()