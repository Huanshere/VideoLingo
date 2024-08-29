import os
import platform
import subprocess
import sys
import zipfile
import shutil
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import SPACY_NLP_MODEL, WHISPER_MODEL

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
                print("未找到lspci命令。正在尝试安装pciutils...")
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
            print("检测到GPU。正在安装支持CUDA的PyTorch...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "torch", "torchvision", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cu118"])
        else:
            print("未检测到GPU。正在安装不支持CUDA的PyTorch...")
            install_package("torch", "torchvision", "torchaudio")
    elif platform.system() == "Darwin":  # macOS
        if "arm" in platform.processor().lower():
            print("检测到Apple Silicon。正在安装支持MLX (Metal)的PyTorch...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--pre", "torch", "torchvision", "torchaudio", "--extra-index-url", "https://download.pytorch.org/whl/nightly/cpu"])
        else:
            print("正在为macOS安装不支持MLX的PyTorch...")
            install_package("torch", "torchvision", "torchaudio")
    elif platform.system() == "Linux":
        if gpu_available:
            print("检测到GPU。正在安装支持CUDA的PyTorch...")
            install_package("torch", "torchvision", "torchaudio")
        else:
            print("未检测到GPU。正在安装不支持CUDA的PyTorch...")  
            install_package("torch", "torchvision", "torchaudio", "--extra-index-url", "https://download.pytorch.org/whl/cpu")
    else:
        print("不支持的平台。请手动安装PyTorch。")

def install_requirements():
    """Install requirements from requirements.txt file."""
    if os.path.exists("requirements.txt"):
        print("正在从requirements.txt安装依赖...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    else:
        print("未找到requirements.txt。跳过安装。")

def download_spacy_model():
    """Download the specified spaCy model."""
    import spacy
    from spacy.cli import download
    try:
        spacy.load(SPACY_NLP_MODEL)
    except:
        print(f"正在下载{SPACY_NLP_MODEL}模型...")
        download(SPACY_NLP_MODEL)

def dowanload_uvr_model():
    """Download the specified uvr model."""
    if not os.path.exists("_model_cache/uvr5_weights/HP2_all_vocals.pth"):
        os.makedirs("_model_cache/uvr5_weights", exist_ok=True)
        import requests
        print("正在下载UVR模型...")
        url = "https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/e992cb1bc5d777fcddce20735a899219b1d46aba/uvr5_weights/HP2_all_vocals.pth"
        response = requests.get(url)
        with open("_model_cache/uvr5_weights/HP2_all_vocals.pth", "wb") as file:
            file.write(response.content)
        print("UVR模型下载成功。")
    else:
        print("HP2_all_vocals.pth已存在。跳过下载。")


def download_sovits_model():
    """Download the specified GPT-SoVITS model files."""
    base_url = "https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/"
    models = {
        "chinese-roberta-wwm-ext-large": ["config.json", "pytorch_model.bin", "tokenizer.json"],
        "chinese-hubert-base": ["config.json", "preprocessor_config.json", "pytorch_model.bin"]
    }

    for model, files in models.items():
        model_dir = os.path.join("_model_cache", "GPT_SoVITS", "pretrained_models", model)
        os.makedirs(model_dir, exist_ok=True)

        for file in files:
            save_path = os.path.join(model_dir, file)
            if os.path.exists(save_path):
                print(f"{file}已存在。跳过下载。")
                continue
            import requests
            url = f"{base_url}{model}/{file}"
            print(f"正在下载{file}...")
            response = requests.get(url)
            if response.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(response.content)
                print(f"{file}下载成功。")
            else:
                print(f"下载{file}失败，状态码：{response.status_code}")

def download_huanyu_model():
    """Download the specified Huanyu model files for GPT-SoVITS."""
    base_url = "https://huggingface.co/Huan69/GPT-SoVITS-Huanyu/resolve/main/"
    model_dir = os.path.join("_model_cache", "GPT_SoVITS", "trained", "Huanyu")
    os.makedirs(model_dir, exist_ok=True)

    files = [
        "huanyushort222-e10.ckpt",
        "huanyushort222_e15_s135.pth",
        "infer_config.json",
        "and to be able to get really good results doing that for a variety of classes.wav"
    ]

    for file in files:
        save_path = os.path.join(model_dir, file)
        if os.path.exists(save_path):
            print(f"{file}已存在。跳过下载。")
            continue

        url = base_url + file
        if file == "and to be able to get really good results doing that for a variety of classes.wav":
            url = base_url + "and%20to%20be%20able%20to%20get%20really%20good%20results%20doing%20that%20for%20a%20variety%20of%20classes.wav"
        import requests
        print(f"正在下载{file}...")
        response = requests.get(url)
        if response.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(response.content)
            print(f"{file}下载成功。")
        else:
            print(f"下载{file}失败，状态码：{response.status_code}")

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
        print("FFmpeg下载仅支持Windows和macOS。")
        return

    if os.path.exists(ffmpeg_exe):
        print(f"{ffmpeg_exe}已存在。跳过下载。")
        return

    print("正在下载FFmpeg...")
    import requests
    response = requests.get(url)
    if response.status_code == 200:
        filename = "ffmpeg.zip"
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"FFmpeg已下载到{filename}")
        
        print("正在解压FFmpeg...")
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
        
        print("正在清理...")
        os.remove(filename)  
        if system != "Linux":
            for item in os.listdir():
                if os.path.isdir(item) and "ffmpeg" in item.lower():
                    shutil.rmtree(item)
        print("FFmpeg解压完成。")
    else:
        print("下载FFmpeg失败")

def main():
    print("开始安装喽...")
    
    # Install requests first
    install_package("requests")
    
    # Check GPU availability
    gpu_available = check_gpu()
    
    # Install PyTorch
    install_torch(gpu_available)
    
    # Install other requirements
    install_requirements()

    # Download nltk for sovits
    import nltk
    nltk.download('averaged_perceptron_tagger_eng')
    
    # Install spaCy model
    install_package("spacy")
    download_spacy_model()
    
    # Download UVR model
    dowanload_uvr_model()

    # Download GPT-SoVITS model
    download_sovits_model()
    download_huanyu_model() # custom model
    
    # Download Whisper model .pt
    import torch
    import whisper_timestamped as whisper
    MODEL_DIR = "./_model_cache"
    device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    os.makedirs(MODEL_DIR, exist_ok=True)
    model = whisper.load_model(WHISPER_MODEL, device=device, download_root=MODEL_DIR)

    # Download and extract FFmpeg
    download_and_extract_ffmpeg()
    
    print("所有安装步骤都完成啦!")

if __name__ == "__main__":
    main()