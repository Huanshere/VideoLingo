__version__ = "2.6.3"

import os,  json
import torch

import logging

from pydantic import BaseModel, Field
logging.getLogger("markdown_it").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("httpcore").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("asyncio").setLevel(logging.ERROR)
logging.getLogger("charset_normalizer").setLevel(logging.ERROR)
logging.getLogger("torchaudio._extension").setLevel(logging.ERROR)
def test_fp16_computation():
    # 检查CUDA是否可用
    if not torch.cuda.is_available():
        return False, "CUDA is not available. Please check your installation."

    try:
        # 创建一个简单的半精度张量计算任务
        # 例如，执行一个半精度的矩阵乘法
        a = torch.randn(3, 3, dtype=torch.float16).cuda()  # 将张量a转换为半精度并移动到GPU
        b = torch.randn(3, 3, dtype=torch.float16).cuda()  # 将张量b转换为半精度并移动到GPU
        c = torch.matmul(a, b)  # 执行半精度的矩阵乘法
        # 如果没有发生错误，我们认为GPU支持半精度运算
        return True, "Your GPU supports FP16 computation."
    except Exception as e:
        # 如果执行过程中发生异常，我们认为GPU不支持半精度运算
        return False, f"Your GPU does not support FP16 computation. Error: {e}"


def get_device_info(device_config="auto", is_half_config="auto")-> tuple[str, bool]:
    global device, is_half
    try:
        return device, is_half
    except:
        if torch.cuda.is_available():
            device = "cuda"
            is_half = True
        else:
            device = "cpu"
            is_half = False

        if device_config != "auto":
            device = device_config
            is_half = (device == "cpu")
        if is_half_config != "auto":
            is_half = str(is_half_config).lower() == "true"

        supports_fp16, message = test_fp16_computation()
        if not supports_fp16 and is_half:
            is_half = False
            print(message)

        return device, is_half




def load_infer_config(character_path):
    config_path = os.path.join(character_path, "infer_config.json")
    """加载环境配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config

def auto_generate_infer_config(character_path):
    ## TODO: Auto-generate wav-list and prompt-list from character_path
    ##     
    # Initialize variables for file detection

    print(f"正在自动生成配置文件: {character_path}")
    ckpt_file_found = None
    pth_file_found = None
    wav_file_found = None

    # Iterate through files in character_path to find matching file types
    for dirpath, dirnames, filenames in os.walk(character_path):
        for file in filenames:
            # 构建文件的完整路径
            full_path = os.path.join(dirpath, file)
            # 从full_path中移除character_path部分
            relative_path = remove_character_path(full_path,character_path)
            # 根据文件扩展名和变量是否已赋值来更新变量
            if file.lower().endswith(".ckpt") and ckpt_file_found is None:
                ckpt_file_found = relative_path
            elif file.lower().endswith(".pth") and pth_file_found is None:
                pth_file_found = relative_path
            elif file.lower().endswith(".wav") and wav_file_found is None:
                wav_file_found = relative_path
            elif file.lower().endswith(".mp3"):
                import pydub
                # Convert mp3 to wav
                wav_file_path = os.path.join(dirpath,os.path.splitext(file)[0] + ".wav")


                pydub.AudioSegment.from_mp3(full_path).export(wav_file_path, format="wav")
                if wav_file_found is None:
                    wav_file_found = remove_character_path(os.path.join(dirpath,os.path.splitext(file)[0] + ".wav"),character_path)
                    

    # Initialize infer_config with gpt_path and sovits_path regardless of wav_file_found
    infer_config = {
        "gpt_path": ckpt_file_found,
        "sovits_path": pth_file_found,
        "software_version": "1.1",
        r"简介": r"这是一个配置文件适用于https://github.com/X-T-E-R/TTS-for-GPT-soVITS，是一个简单好用的前后端项目"
    }

    # If wav file is also found, update infer_config to include ref_wav_path, prompt_text, and prompt_language
    if wav_file_found:
        wav_file_name = os.path.splitext(os.path.basename(wav_file_found))[0]  # Extract the filename without extension
        infer_config["emotion_list"] = {
            "default": {
                "ref_wav_path": wav_file_found,
                "prompt_text": wav_file_name,
                "prompt_language": "多语种混合"
            }
        }
    else:
        raise Exception("找不到wav参考文件！请把有效wav文件放置在模型文件夹下。")
        pass
    # Check if the essential model files were found
    if ckpt_file_found and pth_file_found:
        infer_config_path = os.path.join(character_path, "infer_config.json")
        try:
            with open(infer_config_path , 'w', encoding='utf-8') as f:
                json.dump(infer_config, f, ensure_ascii=False, indent=4)
        except IOError as e:
            print(f"无法写入文件: {infer_config_path}. 错误: {e}")

        return infer_config_path
    else:
        return "Required model files (.ckpt or .pth) not found in character_path directory."


def remove_character_path(full_path,character_path):
    # 从full_path中移除character_path部分
    return os.path.relpath(full_path, character_path)
