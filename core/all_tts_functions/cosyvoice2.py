import os
import sys
import torch
import librosa
import soundfile as sf
from pathlib import Path
from core.config_utils import load_key

model_dir = "pretrained_models/CosyVoice2-0.5B"  # 模型权重目录
sys.path.append(os.path.join(model_dir, "third_party", "Matcha-TTS"))

# 导入 CosyVoice 模型类
from cosyvoice.cli.cosyvoice import CosyVoice  # 假设已成功将模型代码加入路径

def text_to_speech_clone(text: str, refer_audio: str, refer_text: str, output_path: str = "output.wav"):
    """使用 CosyVoice2-0.5B 模型进行零样本语音克隆，将文本合成为模仿参考音色的语音并保存为 WAV 文件。"""
    # 1. 验证输入参数
    if not os.path.isfile(refer_audio):
        raise FileNotFoundError(f"参考音频文件不存在: {refer_audio}")
    if not refer_audio.lower().endswith(".wav"):
        raise ValueError("参考音频文件必须为 WAV 格式")
    if text is None or text.strip() == "":
        raise ValueError("合成的文本不能为空")
    if refer_text is None or refer_text.strip() == "":
        raise ValueError("参考音频的文本转写不能为空")

    # 2. 加载参考音频并重采样到16kHz&#8203;:contentReference[oaicite:6]{index=6}
    # librosa.load 默认将音频转换为单声道，并通过 sr 参数重采样
    audio_data, sr = librosa.load(refer_audio, sr=16000)
    if sr != 16000:
        # 若未能重采样，可自行处理，这里 librosa 已确保 sr=16000
        audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=16000)
        sr = 16000
    # 将 NumPy 数组转换为 PyTorch 张量
    ref_audio_tensor = torch.from_numpy(audio_data)
    if ref_audio_tensor.dim() == 1:
        ref_audio_tensor = ref_audio_tensor.unsqueeze(0)  # shape: (1, N)

    # 3. 加载 CosyVoice2-0.5B 模型权重
    cosyvoice_model = CosyVoice(model_dir, load_jit=False, load_onnx=False, load_trt=False)
    # （提示：如有 GPU，可考虑将模型和张量转移到 CUDA，提高推理速度）

    # 4. 执行零样本语音克隆推理&#8203;:contentReference[oaicite:7]{index=7}
    # 将目标文本、参考文本和参考音频张量传入模型进行推理
    result_iter = cosyvoice_model.inference_zero_shot(text, refer_text, ref_audio_tensor, stream=False)
    # 收集推理结果的语音张量
    outputs = [out["tts_speech"] for out in result_iter]
    if len(outputs) == 0:
        raise RuntimeError("模型未返回任何音频数据")
    # 如果输出分段音频，将它们在时间维度拼接
    tts_audio = torch.cat(outputs, dim=-1)  # 拼接后的语音张量 (shape: [1, T])

    # 将语音张量移动到CPU并转换为 NumPy 数组，准备保存
    tts_audio_np = tts_audio.cpu().squeeze(0).numpy()  # shape: (T,)
    
    # 5. 保存生成的语音为 WAV 文件&#8203;:contentReference[oaicite:8]{index=8}
    sf.write(output_path, tts_audio_np, cosyvoice_model.sample_rate)
    print(f"语音合成完成，已保存输出音频: {output_path}")

def text_to_speech_clone_for_videolingo(text: str, save_as: str, number: int, task_df):
    """使用 CosyVoice2-0.5B 模型进行零样本语音克隆，接口与 gpt_sovits_tts_for_videolingo 保持一致"""
    current_dir = Path.cwd()
    TARGET_LANGUAGE = load_key("target_language")
    WHISPER_LANGUAGE = load_key("whisper.language")
    REFER_MODE = load_key("gpt_sovits.refer_mode")

    # 获取参考文本
    prompt_text = task_df.loc[task_df['number'] == number, 'origin'].values[0]

    # 根据 REFER_MODE 获取参考音频路径
    if REFER_MODE == 1:
        raise NotImplementedError("REFER_MODE 1 is not supported for CosyVoice2 yet")
    elif REFER_MODE in [2, 3]:
        refer_audio = current_dir / ("output/audio/refers/1.wav" if REFER_MODE == 2 else f"output/audio/refers/{number}.wav")
        if not refer_audio.exists():
            try:
                from core.step9_extract_refer_audio import extract_refer_audio_main
                print(f"Reference audio file does not exist, attempting extraction: {refer_audio}")
                extract_refer_audio_main()
            except Exception as e:
                print(f"Failed to extract reference audio: {str(e)}")
                raise

    # 调用原始的 text_to_speech_clone 函数
    text_to_speech_clone(
        text=text,
        refer_audio=str(refer_audio),
        refer_text=prompt_text,
        output_path=save_as
    )

    return True

# 示例调用：
# text_to_speech_clone("你好世界", "reference.wav", "参考音频的文本内容", "cloned_output.wav")
