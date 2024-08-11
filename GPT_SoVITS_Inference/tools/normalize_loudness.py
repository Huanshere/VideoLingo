import soundfile as sf
import numpy as np
from pyloudnorm import Meter, normalize
import os

def normalize_loudness(audio_path, target_loudness, target_path):
    """
    归一化音频文件的响度到指定的目标响度。

    参数:
        audio_path (str): 原始音频文件的路径。
        target_loudness (float): 目标响度值（LUFS）。
        target_path (str): 归一化后音频的保存路径。

    返回:
        bool: 归一化操作是否成功。
    """
    try:
        # 读取音频文件
        data, rate = sf.read(audio_path)

        # 创建响度仪表，基于ITU-R BS.1770
        meter = Meter(rate)  # 采样率

        # 测量音频的响度
        loudness = meter.integrated_loudness(data)

        # 响度归一化
        normalized_audio = normalize.loudness(data, loudness, target_loudness)

        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        # 保存归一化后的音频文件
        sf.write(target_path, normalized_audio, rate)

        return True
    except Exception as e:
        raise e