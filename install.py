import os
import platform
import subprocess
import sys
import zipfile
import shutil
from config import SPACY_NLP_MODEL, WHISPER_MODEL
# Define the spaCy model to be downloaded
SPACY_NLP_MODEL = SPACY_NLP_MODEL

def install_package(*packages):
    subprocess.check_call([sys.executable, "-m", "pip", "install", *packages])

def check_gpu():
    """Check if the system has a GPU."""
    system = platform.system()
    if system == "Windows":
        try:
            output = subprocess.check_output(["wmic", "path", "win32_VideoController", "get", "name"])
            if "nvidia" in output.decode().lower() or "amd" in output.decode().lower():
                return True
        except subprocess.CalledProcessError:
            pass
    elif system == "Darwin":
        try:
            output = subprocess.check_output(["system_profiler", "SPDisplaysDataType"])
            if "vendor: nvidia" in output.decode().lower() or "vendor: amd" in output.decode().lower():
                return True
        except subprocess.CalledProcessError:
            pass
    elif system == "Linux":
        try:
            try:
                output = subprocess.check_output(["lspci"])
            except FileNotFoundError:
                print("lspci command not found. Attempting to install pciutils...")
                subprocess.check_call(["apt-get", "update"])
                subprocess.check_call(["apt-get", "install", "-y", "pciutils"])
                output = subprocess.check_output(["lspci"])

            if "nvidia" in output.decode().lower() or "amd" in output.decode().lower():
                return True
        except subprocess.CalledProcessError:
            pass
    return False

def install_torch(gpu_available):
    """Install PyTorch based on GPU availability and platform."""
    if platform.system() == "Windows":
        if gpu_available:
            print("GPU detected. Installing PyTorch with CUDA support...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "torch", "torchvision", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cu118"])
        else:
            print("No GPU detected. Installing PyTorch without CUDA support...")
            install_package("torch", "torchvision", "torchaudio")
    elif platform.system() == "Darwin":  # macOS
        print("Installing PyTorch for macOS...")
        install_package("torch", "torchvision", "torchaudio")
    elif platform.system() == "Linux":
        if gpu_available:
            print("GPU detected. Installing PyTorch with CUDA support...")
            install_package("torch", "torchvision", "torchaudio")
        else:
            print("No GPU detected. Installing PyTorch without CUDA support...")  
            install_package("torch", "torchvision", "torchaudio", "--extra-index-url", "https://download.pytorch.org/whl/cpu")
    else:
        print("Unsupported platform. Please install PyTorch manually.")

def install_requirements():
    """Install requirements from requirements.txt file."""
    if os.path.exists("requirements.txt"):
        print("Installing requirements from requirements.txt...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    else:
        print("requirements.txt not found. Skipping.")

def download_spacy_model():
    """Download the specified spaCy model."""
    print(f"Downloading spaCy model: {SPACY_NLP_MODEL}")
    subprocess.check_call([sys.executable, "-m", "spacy", "download", SPACY_NLP_MODEL])

def download_and_extract_ffmpeg():
    """Download FFmpeg based on the platform, extract it, and clean up."""
    system = platform.system()
    if system == "Windows":
        ffmpeg_exe = "ffmpeg.exe"
        url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    elif system == "Darwin":
        ffmpeg_exe = "ffmpeg"
        url = "https://evermeet.cx/ffmpeg/ffmpeg-4.4.zip"
    elif system == "Linux":
        ffmpeg_exe = "ffmpeg"
        url = "https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz"
    else:
        print("FFmpeg download is only supported on Windows and macOS.")
        return

    if os.path.exists(ffmpeg_exe):
        print(f"{ffmpeg_exe} already exists. Skipping download.")
        return

    print("Downloading FFmpeg...")
    import requests
    response = requests.get(url)
    if response.status_code == 200:
        filename = "ffmpeg.zip"
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"FFmpeg downloaded to {filename}")
        
        print("Extracting FFmpeg...")
        if system == "Linux":
            import tarfile
            with tarfile.open(filename) as tar_ref:
                for member in tar_ref.getmembers():
                    if member.name.endswith("ffmpeg"):
                        member.name = os.path.basename(member.name)
                        tar_ref.extract(member)
                        break
        else:
            with zipfile.ZipFile(filename, 'r') as zip_ref:
                for file in zip_ref.namelist():
                    if file.endswith(ffmpeg_exe):
                        zip_ref.extract(file)
                        shutil.move(os.path.join(*file.split('/')[:-1], ffmpeg_exe), ffmpeg_exe)
                        break
        
        print("Cleaning up...")
        os.remove(filename)  
        if system != "Linux":
            for item in os.listdir():
                if os.path.isdir(item) and "ffmpeg" in item.lower():
                    shutil.rmtree(item)
        print("FFmpeg extraction complete.")
    else:
        print("Failed to download FFmpeg")

def main():
    print("Starting submagic installation...")
    
    # Install requests first
    install_package("requests")
    
    # Check GPU availability
    gpu_available = check_gpu()
    
    # Install PyTorch
    install_torch(gpu_available)
    
    # Install other requirements
    install_requirements()
    
    # Install spaCy model
    install_package("spacy")
    download_spacy_model()
    
    # Download Whisper model .pt
    import torch
    import whisper_timestamped as whisper
    MODEL_DIR = "./_model_cache"
    device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    os.makedirs(MODEL_DIR, exist_ok=True)
    model = whisper.load_model(WHISPER_MODEL, device=device, download_root=MODEL_DIR)

    # Download and extract FFmpeg
    download_and_extract_ffmpeg()
    
    print("Installation completed successfully!")

if __name__ == "__main__":
    main()