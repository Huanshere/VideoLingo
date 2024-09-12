import os
import platform
import subprocess
import sys
import zipfile
import shutil

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def init_config(api_key, base_url, whisper_method, language):
    """Initialize the config.py file with the specified API key and base URL."""
    if not os.path.exists("config.py"):
        # 从 config.example.py 复制 config.py
        shutil.copy("config.example.py", "config.py")
        print("config.py文件已创建。正在更新API密钥和基础URL。")

        # 读取 config.py 文件内容
        with open("config.py", "r", encoding="utf-8") as file:
            config_content = file.read()

        # 替换 配置项
        config_content = config_content.replace("API_KEY = 'sk-xxx'", f"API_KEY = '{api_key}'")
        config_content = config_content.replace("BASE_URL = 'https://api.deepseek.com'", f"BASE_URL = '{base_url}'")
        config_content = config_content.replace("WHISPER_METHOD = 'whisperxapi'", f"WHISPER_METHOD = '{whisper_method}'")
        config_content = config_content.replace("cloud = 1 if sys.platform.startswith('linux') else 0", "cloud = 0")
        config_content = config_content.replace("DISPLAY_LANGUAGE = 'auto'", f"DISPLAY_LANGUAGE = '{language}'")

        # 将修改后的内容写回 config.py 文件
        with open("config.py", "w", encoding="utf-8") as file:
            file.write(config_content)

        print("config.py文件中的API密钥和基础URL已更新。")
    else:
        print("config.py文件已存在。")


def install_whisper_model(whisper_method):
    if whisper_method == 'whisper_timestamped':
        print("正在安装 whisper_timestamped...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "whisper-timestamped"])
    elif whisper_method == 'whisperX':
        print("正在安装 whisperX...")
        current_dir = os.getcwd()
        whisperx_dir = os.path.join(current_dir, "third_party", "whisperX")
        os.chdir(whisperx_dir)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])
        os.chdir(current_dir)


def main():
    print("开始安装...")

    # 从环境变量中获取 API_KEY 和 BASE_URL
    api_key = os.getenv('API_KEY', 'xxx')
    base_url = os.getenv('BASE_URL', 'https://api.deepseek.com')

    # 用户选择 Whisper 模型
    whisper_method = os.getenv('WHISPER_METHOD', 'whisper_timestamped')

    # 语言
    language = os.getenv('DISPLAY_LANGUAGE', 'auto')

    # 初始化 config.py 文件
    init_config(api_key, base_url, whisper_method, language)

    # 安装选择的 Whisper 模型
    install_whisper_model(whisper_method)

    print("所有安装步骤都完成啦!")


if __name__ == "__main__":
    main()
