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
from core.pypi_autochoose.pypi_autochoose import main as choose_mirror

def main():

    choose_mirror()
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel

    console = Console()
    console.print(Panel.fit("Starting installation...", style="bold magenta"))

    def init_language():
        import locale
        from core.config_utils import load_key, update_key
        system_lang = locale.getdefaultlocale()[0]
        lang_map = {
            'zh_CN': 'zh_CN', 'zh_TW': 'zh_CN',
            'en_US': 'en_US', 'ja_JP': 'ja_JP'
        }
        display_language = lang_map.get(system_lang, 'en_US')
        if load_key("display_language") == "auto":
            update_key("display_language", display_language)
            console.print(Panel.fit("Display language set to system language: " + display_language, style="bold green"))

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
        """Download the specified uvr models."""
        models = {
            "HP2_all_vocals.pth": "https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/e992cb1bc5d777fcddce20735a899219b1d46aba/uvr5_weights/HP2_all_vocals.pth",
            "VR-DeEchoAggressive.pth": "https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/uvr5_weights/VR-DeEchoAggressive.pth"
        }
        os.makedirs("_model_cache/uvr5_weights", exist_ok=True)
        import requests
        for model_name, url in models.items():
            model_path = f"_model_cache/uvr5_weights/{model_name}"
            if not os.path.exists(model_path):
                print(f"Downloading UVR model: {model_name}...")
                response = requests.get(url, stream=True)
                total_size = int(response.headers.get('content-length', 0))
                with open(model_path, "wb") as file:
                    for data in response.iter_content(chunk_size=4096):
                        size = file.write(data)
                        print(f"Downloaded: {(size/total_size)*100:.2f}%", end="\r")
                print(f"\n{model_name} downloaded successfully.")
            else:
                print(f"{model_name} already exists. Skipping download.")

    def download_and_extract_ffmpeg():
        """Download FFmpeg based on the platform, extract it, and clean up."""
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
            print(f"{ffmpeg_exe} already exists. Skipping download.")
            return

        print("Downloading FFmpeg...")
        import requests

        response = requests.get(url)
        if response.status_code == 200:
            filename = "ffmpeg.zip" if system in ["Windows", "Darwin"] else "ffmpeg.tar.xz"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"FFmpeg has been downloaded to {filename}")
        
            print("Extracting FFmpeg...")
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
            
            print("Cleaning up...")
            os.remove(filename)
            if system == "Windows":
                for item in os.listdir():
                    if os.path.isdir(item) and "ffmpeg" in item.lower():
                        shutil.rmtree(item)
            print("FFmpeg extraction completed.")
        else:
            print("Failed to download FFmpeg")

    def install_noto_font():
        if platform.system() == 'Linux':
            # 如果字体未安装，安装 Noto 字体
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'fonts-noto'], check=True)
    
    # User selects Whisper model
    table = Table(title="Whisper Model Selection")
    table.add_column("Option", style="cyan", no_wrap=True)
    table.add_column("Model", style="magenta")
    table.add_column("Description", style="green")
    table.add_row("1", "whisperX 💻", "local model (can also use online model api)")
    table.add_row("2", "whisperXapi ☁️", "online model through api only")
    console.print(table)

    console.print("If you're unsure about the differences between models, please see https://github.com/Huanshere/VideoLingo/")

    # check if the user has provided the choice as a command line argument
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = console.input("Please enter the option number (1 or 2): ")

    # Install PyTorch and WhisperX
    if platform.system() == 'Darwin':  # macOS do not support Nvidia CUDA
        console.print(Panel("For MacOS, installing CPU version of PyTorch...", style="cyan"))
        subprocess.check_call([sys.executable, "-m", "pip", "install", "torch", "torchaudio"])
        if choice == '1':
            print("Installing whisperX...")
            current_dir = os.getcwd()
            whisperx_dir = os.path.join(current_dir, "third_party", "whisperX")
            os.chdir(whisperx_dir)
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])
            os.chdir(current_dir)
    else:  # Linux/Windows
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

    # Initialize display language
    init_language()

    # Install noto font
    install_noto_font()

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