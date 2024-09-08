import os
import sys
from typing import Union
import importlib

# 添加必要的路径
now_dir = os.getcwd()
sys.path.append(now_dir)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.common_config_manager import api_config
from Synthesizers.base import Base_TTS_Synthesizer


# 全局变量
tts_synthesizer: Base_TTS_Synthesizer = None

def init_model():
    """
    初始化 TTS 模型
    """
    global tts_synthesizer
    # 动态导入合成器模块
    synthesizer_name = api_config.synthesizer
    synthesizer_module = importlib.import_module(f"Synthesizers.{synthesizer_name}")
    TTS_Synthesizer = synthesizer_module.TTS_Synthesizer
    
    # 初始化合成器
    tts_synthesizer = TTS_Synthesizer(debug_mode=True)

    # 生成一句话充当测试，减少第一次请求的等待时间
    gen = tts_synthesizer.generate(tts_synthesizer.params_parser({"text": "你好，世界"}))
    next(gen)

def unload_model():
    """
    卸载 TTS 模型
    """
    global tts_synthesizer
    if tts_synthesizer:
        del tts_synthesizer
        tts_synthesizer = None

def tts_function(text: str, 
            character: str = None,
            speed: float = 1.0,
            format: str = "wav",
            save_path: str = None,
            **kwargs) -> Union[str, bytes]:
    """
    将文本转换为语音。

    Args:
        text (str): 要合成的文本。
        character (str, optional): TTS 角色。默认为 None。
        speed (float, optional): 语速，默认为 1.0。
        format (str, optional): 音频格式，默认为 "wav"。
        save_path (str, optional): 指定保存音频文件的路径。默认为 None，使用系统临时目录。
        **kwargs: 其他合成器特定的参数。

    Returns:
        Union[str, bytes]: 生成的音频文件路径或音频数据。
    """
    global tts_synthesizer
    
    if not tts_synthesizer:
        raise ValueError("TTS 模型未初始化，请先调用 init_model() 函数")

    # 构建 TTS 任务参数
    task_params = {
        "text": text,
        "character": character,
        "format": format,
        "speed": speed,
        **kwargs
    }

    # 使用 params_parser 创建任务
    task = tts_synthesizer.params_parser(task_params)

    # 生成音频
    if save_path:
        # 确保目录存在
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        audio_file = tts_synthesizer.generate(task, return_type="filepath", save_path=save_path)
    else:
        audio_file = tts_synthesizer.generate(task, return_type="filepath")

    return audio_file

if __name__ == "__main__":
    custom_path = os.path.join(os.getcwd(), "output", "custom_audio.wav")

    # 切换目录到当前文件所在目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    # 初始化模型
    init_model()

    # 测试例子
    text = "你好，我是许环宇的数字人分身！"
    character = "Huanyu"  
    speed = 1.0

    # 使用自定义路径
    
    audio_file = tts_function(text, character=character, speed=speed, save_path=custom_path)
    
    print(f"生成的音频文件（自定义路径）：{audio_file}")

    # 卸载模型
    unload_model()
    # 切换回原来的目录
    os.chdir(now_dir)