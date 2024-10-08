import os
import platform
import subprocess
import sys
import zipfile
import shutil
import locale
import requests
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def install_package(*packages):
    subprocess.check_call([sys.executable, "-m", "pip", "install", *packages])

install_package("requests", "rich", "ruamel.yaml")
from core.pypi_autochoose.pypi_autochoose import main as choose_mirror

def load_language(lang='en'):
    from ruamel.yaml import YAML
    yaml = YAML(typ='safe')
    try:
        with open(f'language/lang_{lang}.yml', 'r', encoding='utf-8') as f:
            return yaml.load(f)
    except FileNotFoundError:
        print(f"Language file for {lang} not found. Falling back to English.")
        with open('language/lang_en.yml', 'r', encoding='utf-8') as f:
            return yaml.load(f)

def main():
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel

    console = Console()

    # Determine language based on system locale
    system_lang = locale.getdefaultlocale()[0]
    lang = 'zh' if system_lang.startswith('zh') else 'en'
    
    # Load language strings
    strings = load_language(lang)

    console.print(Panel.fit(strings['starting_installation'], style="bold magenta"))

    # Ask if user is in China
    in_china = console.input(strings['ask_in_china'])

    if in_china == "1":
        console.print(Panel(strings['configuring_mirror'], style="bold yellow"))
        choose_mirror()
    else:
        console.print(Panel(strings['skipping_mirror'], style="bold blue"))

    def init_language():
        from core.config_utils import load_key, update_key
        system_lang = locale.getdefaultlocale()[0]
        lang_map = {
            'zh_CN': 'zh_CN', 'zh_TW': 'zh_CN',
            'en_US': 'en_US', 'ja_JP': 'ja_JP'
        }
        display_language = lang_map.get(system_lang, 'en_US')
        if load_key("display_language") == "auto":
            update_key("display_language", display_language)
            console.print(Panel.fit(f"{strings['display_language_set']}{display_language}", style="bold green"))

    def install_requirements():
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
            
            print(strings['installing_dependencies'])
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        else:
            print(strings['requirements_not_found'])

    def test_mirror_speed(name, base_url):
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
                time.sleep(1)  # 在重试之前等待1秒

    return name, float('inf')

    
    def download_uvr_model():
        models = {
            "HP2_all_vocals.pth": "lj1995/VoiceConversionWebUI/resolve/e992cb1bc5d777fcddce20735a899219b1d46aba/uvr5_weights/HP2_all_vocals.pth",
            "VR-DeEchoAggressive.pth": "lj1995/VoiceConversionWebUI/resolve/main/uvr5_weights/VR-DeEchoAggressive.pth"
        }
        
        mirrors = {
            "Official": "https://huggingface.co/",
            "Mirror": "https://hf-mirror.com/"
        }
    
        os.makedirs("_model_cache/uvr5_weights", exist_ok=True)
    
        for model_name, model_path in models.items():
            model_file_path = f"_model_cache/uvr5_weights/{model_name}"
            if not os.path.exists(model_file_path):
                print(f"{strings['downloading_uvr_model']}{model_name}...")
                
                # Test speed for each mirror
                speeds = []
                for mirror_name, mirror_url in mirrors.items():
                    test_url = mirror_url + model_path
                    name, speed = test_mirror_speed(mirror_name, test_url)
                    speeds.append((name, speed))
                    print(f"{mirror_name} mirror speed: {speed:.2f} ms")
    
                # Choose the fastest mirror
                fastest_mirror = min(speeds, key=lambda x: x[1])[0]
                print(f"Choosing {fastest_mirror} mirror for download.")
    
                # Download from the fastest mirror
                url = mirrors[fastest_mirror] + model_path
                response = requests.get(url, stream=True)
                total_size = int(response.headers.get('content-length', 0))
                
                with open(model_file_path, "wb") as file:
                    downloaded_size = 0
                    for data in response.iter_content(chunk_size=4096):
                        size = file.write(data)
                        downloaded_size += size
                        print(f"Downloaded: {(downloaded_size/total_size)*100:.2f}%", end="\r")
                
                print(f"\n{model_name} {strings['model_downloaded']}")
            else:
                print(f"{model_name} {strings['model_exists']}")

    def download_and_extract_ffmpeg():
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
            print(f"{ffmpeg_exe} {strings['ffmpeg_exists']}")
            return

        print(strings['downloading_ffmpeg'])
        import requests

        response = requests.get(url)
        if response.status_code == 200:
            filename = "ffmpeg.zip" if system in ["Windows", "Darwin"] else "ffmpeg.tar.xz"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"{strings['ffmpeg_downloaded']}{filename}")
        
            print(strings['extracting_ffmpeg'])
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
            
            print(strings['cleaning_up'])
            os.remove(filename)
            if system == "Windows":
                for item in os.listdir():
                    if os.path.isdir(item) and "ffmpeg" in item.lower():
                        shutil.rmtree(item)
            print(strings['ffmpeg_extraction_completed'])
        else:
            print(strings['failed_download_ffmpeg'])

    def install_noto_font():
        if platform.system() == 'Linux':
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'fonts-noto'], check=True)
    
    # User selects Whisper model
    table = Table(title=strings['whisper_model_selection'])
    table.add_column(strings['option'], style="cyan", no_wrap=True)
    table.add_column(strings['model'], style="magenta")
    table.add_column(strings['description'], style="green")
    table.add_row("1", "whisperX 💻", strings['whisperx_local'])
    table.add_row("2", "whisperXapi ☁️", strings['whisperxapi_cloud'])
    console.print(table)

    console.print(strings['model_difference_info'])

    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = console.input(strings['enter_option'])

    if platform.system() == 'Darwin':
        console.print(Panel(strings['installing_cpu_pytorch'], style="cyan"))
        subprocess.check_call([sys.executable, "-m", "pip", "install", "torch", "torchaudio"])
        if choice == '1':
            print(strings['installing_whisperx'])
            current_dir = os.getcwd()
            whisperx_dir = os.path.join(current_dir, "third_party", "whisperX")
            os.chdir(whisperx_dir)
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])
            os.chdir(current_dir)
    else:
        if choice == '1':
            console.print(Panel(strings['installing_cuda_pytorch'], style="cyan"))
            subprocess.check_call([sys.executable, "-m", "pip", "install", "torch==2.0.0", "torchaudio==2.0.0", "--index-url", "https://download.pytorch.org/whl/cu118"])

            print(strings['installing_whisperx'])
            current_dir = os.getcwd()
            whisperx_dir = os.path.join(current_dir, "third_party", "whisperX")
            os.chdir(whisperx_dir)
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])
            os.chdir(current_dir)
        elif choice == '2':
            table = Table(title=strings['pytorch_version_selection'])
            table.add_column(strings['option'], style="cyan", no_wrap=True)
            table.add_column(strings['model'], style="magenta")
            table.add_column(strings['description'], style="green")
            table.add_row("1", "CPU", strings['cpu_version'])
            table.add_row("2", "GPU", strings['gpu_version'])
            console.print(table)

            torch_choice = console.input(strings['enter_pytorch_option'])
            if torch_choice == '1':
                console.print(Panel(strings['installing_cpu_pytorch_message'], style="cyan"))
                subprocess.check_call([sys.executable, "-m", "pip", "install", "torch", "torchaudio"])
            elif torch_choice == '2':
                console.print(Panel(strings['installing_gpu_pytorch_message'], style="cyan"))
                subprocess.check_call([sys.executable, "-m", "pip", "install", "torch", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cu118"])
            else:
                console.print(strings['invalid_choice'])
                subprocess.check_call([sys.executable, "-m", "pip", "install", "torch", "torchaudio"])
        else:
            raise ValueError(strings['invalid_choice_retry'])

    init_language()
    install_noto_font()
    install_requirements()
    download_uvr_model()  
    download_and_extract_ffmpeg()
    
    console.print(Panel.fit(strings['installation_completed'], style="bold green"))
    console.print(strings['start_streamlit_command'])
    console.print("[bold cyan]streamlit run st.py[/bold cyan]")

if __name__ == "__main__":
    main()
