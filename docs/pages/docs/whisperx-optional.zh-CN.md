# WhisperX（可选备选）

VideoLingo 默认的本地语音识别是 **Qwen3-ASR + Qwen3-ForcedAligner**，见[使用文档](start.zh-CN.md#asr-runtime)。WhisperX 仍保留为可选备选：代码路径和行为不变（包括中文强制使用 Belle 模型），但**默认安装不再包含 WhisperX**，`installer.py` 也不会安装或要求它。

以下情况可以考虑改用 WhisperX：想和 Qwen 的结果做对比；希望中文使用带标点增强的 Belle Whisper 模型；已有基于 WhisperX 的使用习惯。

## 支持范围

| 平台 | 能否与默认环境共存 | 说明 |
|:-----|:-------------------|:-----|
| Windows / Linux | 可以 | 在 VideoLingo 环境中追加安装，见下文。依赖解析已用 `uv pip compile` 验证（Python 3.13），未在本仓库环境中实跑识别 |
| Apple Silicon Mac | **不可以** | 默认的 MLX 后端需要 `huggingface-hub>=1`，WhisperX 3.8.6 需要 `huggingface-hub<1`。请**另建一个独立环境**使用 WhisperX，不要装进默认环境 |

## 安装

在已经用 `setup_env.py` 装好的 VideoLingo 环境里执行（以项目 `.venv` 为例；使用 `--shared` 共享环境时，把路径换成 `~/.venvs/videolingo`）：

```bash
# Windows
.venv\Scripts\python -m pip install "whisperx>=3.8.6,<3.9" "ctranslate2>=4.5,<5" "pyannote-audio>=4.0.4,<5" "torchcodec>=0.7,<0.8"
# Linux
.venv/bin/python -m pip install "whisperx>=3.8.6,<3.9" "ctranslate2>=4.5,<5" "pyannote-audio>=4.0.4,<5" "torchcodec>=0.7,<0.8"
```

这 4 个包的版本约束与 3.0.4 版本中 `requirements.txt` 的约束相同。WhisperX 3.8 需要 Torch/torchaudio 2.8、torchvision 0.23 和 Transformers 4，与默认环境一致，因此不需要改动已装的 PyTorch。

安装后执行 `python installer.py --check`。只要环境里装了 whisperx，检查就会额外探测 TorchCodec 能否加载 FFmpeg 共享库；没有装 whisperx 时跳过这一项。在 Windows / Linux 上，以后重跑 `installer.py` 或 `--upgrade` 不会卸载 WhisperX，如果检查报错，重新执行上面的安装命令即可。在 Apple Silicon 上，重跑 `installer.py` 会主动卸载默认环境里的 whisperx 和 torchcodec，见下文。

## 启用

在侧栏选择「语音识别运行环境：本地」→「本地识别后端：WhisperX（可选备选）」，或在 `config.yaml` 中设置：

```yaml
whisper:
  runtime: 'local'
  backend: 'whisperx'
  model: 'large-v3'   # 或 large-v3-turbo；仅 WhisperX 使用
  language: 'en'
```

- 识别语言设为 `zh` 时，WhisperX 路径会强制使用 `Huan69/Belle-whisper-large-v3-zh-punct-fasterwhisper`，忽略 `whisper.model`。
- 自动检测到中文但识别语言不是 `zh` 时，WhisperX 路径会报错，要求明确选择中文。
- 识别结果缓存的键包含后端，WhisperX 和 Qwen 的结果不会互相复用。

<a id="cuda-runtime"></a>
## GPU 运行库（CUDA 12 cuBLAS / cuDNN 9）

默认的 Qwen 路径只需要 PyTorch 自带的 CUDA 运行库。WhisperX 使用 CTranslate2（faster-whisper），GPU 运行时还需要进程能找到 **CUDA 12 cuBLAS 和 cuDNN 9**。依据为 [faster-whisper GPU 要求](https://github.com/SYSTRAN/faster-whisper#gpu)和 [CTranslate2 4.5 的 cuDNN 9 变更](https://github.com/OpenNMT/CTranslate2/releases/tag/v4.5.0)。

- Windows 缺少这些库时，可从 NVIDIA 的 [CUDA 12.8 Update 1 归档](https://developer.nvidia.com/cuda-12-8-1-download-archive)取得 CUDA 12 库，从 [NVIDIA](https://developer.nvidia.com/cudnn-downloads)选择 **用于 CUDA 12 的 cuDNN 9**。将实际 DLL 所在目录加入 PATH 后重开终端，不能把 PyTorch 包版本直接替换进示例 cuDNN 路径。
- Linux 按上述 faster-whisper 文档，在启动 Python 前通过 `LD_LIBRARY_PATH` 暴露已安装的 cuBLAS/cuDNN 库。Docker 镜像基于 `cudnn-runtime`，已包含这些运行库。

<a id="ffmpeg-runtime"></a>
## FFmpeg 共享库（TorchCodec 0.7）

WhisperX 链路（pyannote）通过 TorchCodec 加载 FFmpeg **共享库**，只有 FFmpeg 命令行程序不够。固定的 TorchCodec 0.7 支持 FFmpeg 4–7，不支持 FFmpeg 8/9，请使用 FFmpeg 7 共享库版。

Windows 上已实际下载并完成音频解码验证的构建为
[BtbN 7.1 共享库版](https://github.com/BtbN/FFmpeg-Builds/releases/download/autobuild-2025-07-31-14-15/ffmpeg-n7.1.1-56-gc2184b65d2-win64-gpl-shared-7.1.zip)。
解压后将其 `bin` 目录放在 PATH 中其他 FFmpeg 版本之前。VideoLingo 会将该目录登记为 Windows DLL 搜索目录。包管理器可能提供更新但不兼容的版本，需要核对。

## Apple Silicon：另建环境

在 Apple Silicon 上，默认依赖会安装 mlx-audio（要求 Transformers 5、`huggingface-hub>=1`），而 WhisperX 3.8.6 要求 `huggingface-hub<1`，两者不能装在同一个环境里。`uv` 只有选中预发布版 whisperx 3.8.7rc1 才能解出依赖，该组合未经验证，不建议使用。

如需在 Mac 上使用 WhisperX，请为它另建一个独立的虚拟环境，不要在默认环境里执行上面的安装命令。本仓库不提供这个独立环境的安装脚本，相关组合也没有经过验证。如果默认环境里已经装了 whisperx（例如从旧版本升级），重跑 `installer.py` 时会先卸载 whisperx 和 torchcodec，`installer.py --check` 也会把两者共存判为错误。

<a id="common-errors"></a>
## 常见报错

1. **`local_files_only=True`**：所选 Whisper 本地模型或缓存不完整。检查模型目录及 `config.json`、`model.bin`、`tokenizer.json`，离线查找不能下载缺失权重，ping 成功也不能证明模型可用。
2. **`cublas64_12.dll not found`**：进程找不到 CUDA 12 cuBLAS。按上面的 [GPU 运行库](#cuda-runtime) 核对实际启动环境、Torch CUDA 包和库搜索路径，仅更新驱动不提供这个 DLL。
3. **Whisper 模型加载时无报错直接段错误 (Segfault)**：ctranslate2 版本与 cuDNN 版本不匹配。确保 `ctranslate2>=4.5.0`（支持 cuDNN 9，PyTorch 2.6+ 自带 cuDNN 9）。
4. **`RuntimeError: Weights only load failed`**：PyTorch ≥2.6 更改了 `torch.load` 的默认行为。已在 `whisperX_local.py` 中通过猴补丁修复，如果遇到此问题说明代码未正确更新。
5. **Streamlit 中 WhisperX 转录卡住不动（CPU/GPU 均空闲）**：`librosa.load()` 在 Streamlit 的非主线程中死锁。已用 `whisperx.audio.load_audio()`（基于 ffmpeg 子进程）替换。如果遇到此问题说明代码未正确更新。
6. **TorchCodec could not load**：`installer.py --check` 的 TorchCodec 探测失败，通常是 FFmpeg 版本为 8/9 或只有命令行程序没有共享库。按上面的 [FFmpeg 共享库](#ffmpeg-runtime) 处理。
7. **`No module named 'whisperx'`**：选择了 WhisperX 后端但没有安装，按上面的安装步骤安装，或在侧栏切回 Qwen3-ASR。
