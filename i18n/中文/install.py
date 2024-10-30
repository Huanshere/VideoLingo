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

    console.print(Panel.fit("开始安装", style="bold magenta"))

    # 执行镜像配置
    console.print(Panel("配置镜像", style="bold yellow"))
    choose_mirror()

    def install_requirements():
        try:
            with open("requirements.txt", "r", encoding="utf-8") as file:
                content = file.read()
            with open("requirements.txt", "w", encoding="gbk") as file:
                file.write(content)
        except Exception as e:
            print(f"转换 requirements.txt 时出错：{str(e)}")
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
                time.sleep(1)  # 重试前等待1秒

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
            print(f"{ffmpeg_exe} 已存在")
            return

        print("正在下载 FFmpeg")
        response = requests.get(url)
        if response.status_code == 200:
            filename = "ffmpeg.zip" if system in ["Windows", "Darwin"] else "ffmpeg.tar.xz"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"FFmpeg 已下载：{filename}")
        
            print("正在解压 FFmpeg")
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
            
            print("清理中")
            os.remove(filename)
            if system == "Windows":
                for item in os.listdir():
                    if os.path.isdir(item) and "ffmpeg" in item.lower():
                        shutil.rmtree(item)
            print("FFmpeg 解压完成")
        else:
            print("下载 FFmpeg 失败")

    def install_noto_font():
        if platform.system() == 'Linux':
            try:
                # 首先尝试 apt-get（基于 Debian 的系统）
                subprocess.run(['sudo', 'apt-get', 'install', '-y', 'fonts-noto'], check=True)
                print("使用 apt-get 成功安装 Noto 字体。")
            except subprocess.CalledProcessError:
                try:
                    # 如果 apt-get 失败，尝试 yum（基于 RPM 的系统）
                    subprocess.run(['sudo', 'yum', 'install', '-y', 'fonts-noto'], check=True)
                    print("使用 yum 成功安装 Noto 字体。")
                except subprocess.CalledProcessError:
                    print("自动安装 Noto 字体失败。请手动安装。")

    # 用户选择 Whisper 模型
    table = Table(title="Whisper 模型选择")
    table.add_column("选项", style="cyan", no_wrap=True)
    table.add_column("模型", style="magenta")
    table.add_column("描述", style="green")
    table.add_row("1", "whisperX 💻", "使用 whisperX 进行本地处理")
    table.add_row("2", "whisperXapi ☁️", "使用 whisperXapi 进行云处理")
    console.print(table)

    console.print("WhisperX 在您的机器上本地处理音频，而 whisperXapi 使用云处理。")

    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = console.input("请输入您的选择（1 或 2）：")

    if platform.system() == 'Darwin':
        console.print(Panel("对于 MacOS，正在安装 CPU 版本的 PyTorch...", style="cyan"))
        subprocess.check_call([sys.executable, "-m", "pip", "install", "torch", "torchaudio"])
        if choice == '1':
            print("正在安装 whisperX...")
            current_dir = os.getcwd()
            whisperx_dir = os.path.join(current_dir, "third_party", "whisperX")
            os.chdir(whisperx_dir)
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])
            os.chdir(current_dir)
    else:
        if choice == '1':
            console.print(Panel("正在安装支持 CUDA 的 PyTorch...", style="cyan"))
            subprocess.check_call([sys.executable, "-m", "pip", "install", "torch==2.0.0", "torchaudio==2.0.0", "--index-url", "https://download.pytorch.org/whl/cu118"])

            print("正在安装 whisperX...")
            current_dir = os.getcwd()
            whisperx_dir = os.path.join(current_dir, "third_party", "whisperX")
            os.chdir(whisperx_dir)
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])
            os.chdir(current_dir)
        elif choice == '2':
            table = Table(title="PyTorch 版本选择")
            table.add_column("选项", style="cyan", no_wrap=True)
            table.add_column("模型", style="magenta")
            table.add_column("描述", style="green")
            table.add_row("1", "CPU", "如果您使用 Mac、非 NVIDIA GPU 或不需要 GPU 加速，请选择此项")
            table.add_row("2", "GPU", "显著加快 音分离速度。如果您需要配音功能并且有 NVIDIA GPU，强烈推荐。")
            console.print(table)

            torch_choice = console.input("请输入选项编号（1 表示 CPU，2 表示 GPU）：")
            if torch_choice == '1':
                console.print(Panel("正在安装 CPU 版本的 PyTorch...", style="cyan"))
                subprocess.check_call([sys.executable, "-m", "pip", "install", "torch", "torchaudio"])
            elif torch_choice == '2':
                console.print(Panel("正在安装支持 CUDA 11.8 的 GPU 版本 PyTorch...", style="cyan"))
                subprocess.check_call([sys.executable, "-m", "pip", "install", "torch", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cu118"])
            else:
                console.print("无效选择。默认使用 CPU 版本。")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "torch", "torchaudio"])
        else:
            raise ValueError("无效选择。请输入 1 或 2。请重试。")

    install_noto_font()
    install_requirements()
    download_and_extract_ffmpeg()
    
    console.print(Panel.fit("安装完成", style="bold green"))
    console.print("要启动应用程序，请运行：")
    console.print("[bold cyan]streamlit run st.py[/bold cyan]")

if __name__ == "__main__":
    main()
