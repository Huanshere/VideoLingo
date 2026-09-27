# WhisperX (manual install)

VideoLingo's default local speech recognition is **Qwen3-ASR + Qwen3-ForcedAligner**; see the [Start guide](start.en-US.md#asr-runtime). WhisperX is still a local backend (`whisper.backend: whisperx`), including the forced Belle model for Chinese, but it is **not an installer option**. `setup_env.py` and `installer.py` do not install it, do not ask whether to install it, and have no flag for it. This page is the only install guide: you install the extra packages yourself.

Consider WhisperX when you want to compare against Qwen, want the punctuation-enhanced Belle Whisper model for Chinese, or already rely on a WhisperX-based workflow.

## Support

| Platform | Same environment as the default? | Notes |
|:---------|:---------------------------------|:------|
| Windows / Linux | Yes | Add it to the VideoLingo environment as shown below. Dependency resolution was verified with `uv pip compile` (Python 3.13); Windows CPU recognition, pyannote VAD and alignment were verified without system FFmpeg or working TorchCodec; Linux inference has not been run |
| Apple Silicon Mac | **No** | The default MLX backend needs `huggingface-hub>=1`; WhisperX 3.8.6 needs `huggingface-hub<1`. Create a **separate environment** for WhisperX instead of installing it into the default one |

## Install

These commands are for you to run. The installer will not run them and will not install WhisperX back later.

On Windows or Linux, run this inside the VideoLingo environment created by `setup_env.py` (the project `.venv` is shown; for a `--shared` environment use `~/.venvs/videolingo`). Do not run them in the default Apple Silicon environment; use a separate environment, as described below.

```bash
# Windows
.venv\Scripts\python -m pip install "whisperx>=3.8.6,<3.9" "ctranslate2>=4.5,<5" "pyannote-audio>=4.0.4,<5" "torchcodec>=0.7,<0.8"
# Linux
.venv/bin/python -m pip install "whisperx>=3.8.6,<3.9" "ctranslate2>=4.5,<5" "pyannote-audio>=4.0.4,<5" "torchcodec>=0.7,<0.8"
```

These are the same constraints `requirements.txt` used in 3.0.4. WhisperX 3.8 needs Torch/torchaudio 2.8, torchvision 0.23 and Transformers 4, which match the default environment, so the installed PyTorch build does not change.

After enabling the local WhisperX backend below, run `python installer.py --check` in that same environment. The check exercises FFmpeg decoding and pyannote's in-memory audio path; it does not require TorchCodec's file decoder. On Windows/Linux, rerunning `installer.py` or `--upgrade` does not uninstall WhisperX packages you added yourself. On Apple Silicon, rerunning the installer in the default environment removes the incompatible WhisperX stack (see below).

## Enable

In the sidebar choose "ASR Runtime: Local" → "Local ASR Backend: WhisperX (manual install)", or set in `config.yaml`:

```yaml
whisper:
  runtime: 'local'
  backend: 'whisperx'
  model: 'large-v3'   # WhisperX only. large-v3-turbo is rewritten to large-v3
  language: 'en'
```

- `whisper.model` accepts `large-v3`. A name containing `turbo` (including `large-v3-turbo`) is rewritten to `large-v3` before loading, because turbo loops on repeated words in this pipeline. The cache key uses `large-v3` as well.
- With recognition language `zh`, the WhisperX path forces `Huan69/Belle-whisper-large-v3-zh-punct-fasterwhisper` and ignores `whisper.model`.
- If Chinese is detected while the recognition language is not `zh`, the WhisperX path stops and asks you to select Chinese explicitly.
- The transcription cache key includes the backend, so WhisperX and Qwen results are never reused for each other.

<a id="cuda-runtime"></a>
## GPU runtime (CUDA 12 cuBLAS / cuDNN 9)

The default Qwen path only needs the CUDA runtime bundled with PyTorch. WhisperX uses CTranslate2 (faster-whisper), whose GPU execution also needs **CUDA 12 cuBLAS and cuDNN 9** accessible to the process. See [faster-whisper's GPU requirements](https://github.com/SYSTRAN/faster-whisper#gpu) and [CTranslate2 4.5's cuDNN 9 transition](https://github.com/OpenNMT/CTranslate2/releases/tag/v4.5.0).

- If the libraries are missing on Windows, obtain CUDA 12 libraries from NVIDIA's [CUDA 12.8 Update 1 archive](https://developer.nvidia.com/cuda-12-8-1-download-archive) and cuDNN 9 **for CUDA 12** from [NVIDIA](https://developer.nvidia.com/cudnn-downloads). Add the actual DLL directories to PATH and reopen the terminal. Do not invent a cuDNN directory by substituting the PyTorch build tag into an example path.
- On Linux, follow faster-whisper's linked instructions for exposing the installed cuBLAS/cuDNN libraries through `LD_LIBRARY_PATH` before starting Python. The Docker image is based on `cudnn-runtime` and includes these libraries.

<a id="ffmpeg-runtime"></a>
## FFmpeg: no manual installation

WhisperX in VideoLingo reuses the FFmpeg CLI automatically provided by the installer. It decodes files with `whisperx.audio.load_audio`, then passes NumPy audio to transcription/alignment. WhisperX passes an in-memory `waveform` and `sample_rate` to pyannote, which officially supports this even when TorchCodec cannot load. No extra shared FFmpeg build or PATH configuration is required for this pipeline.

This was verified on Windows with WhisperX 3.8.6, pyannote-audio 4.0.7 and TorchCodec 0.7.0: system PATH cleared, managed FFmpeg 8.0.1 enabled, and TorchCodec import confirmed to fail. The actual VideoLingo backend completed a 15.05-second English sample with tiny.en on CPU, pyannote VAD and word alignment (35 words). Large/Belle models and Linux/macOS inference were not exercised in this experiment.

TorchCodec remains installed to satisfy pyannote's Python package dependencies. Its shared-library decoder is only needed if custom code asks TorchCodec or pyannote to read filenames directly. That separate usage requires compatible shared libraries (TorchCodec 0.7 supports FFmpeg 4–7); the managed static executable does not provide them. On Windows, the optional `VIDEOLINGO_FFMPEG_DLL_DIR` override remains available for such custom usage. See [pyannote's audio input implementation](https://github.com/pyannote/pyannote-audio/blob/4.0.4/src/pyannote/audio/core/io.py).

## Apple Silicon: use a separate environment

On Apple Silicon the default requirements install mlx-audio (Transformers 5, `huggingface-hub>=1`), while WhisperX 3.8.6 requires `huggingface-hub<1`, so they cannot share one environment. `uv` only resolves the combination by picking the pre-release whisperx 3.8.7rc1, which is unverified and not recommended.

To use WhisperX on a Mac, create a separate virtual environment for it; do not run the install command above in the default environment. This repository does not ship an installer for that separate environment, and the combination has not been verified. If the default environment already has whisperx (for example after upgrading from an older version), rerunning `installer.py` first uninstalls the WhisperX stack (whisperx, torchcodec, faster-whisper, ctranslate2, pyannote-*) (packages that another installed package still requires are kept). The installer will not install WhisperX again. `installer.py --check` reports the combination as an error until that stack is gone.

<a id="common-errors"></a>
## Common errors

1. **`local_files_only=True`**: The selected local Whisper model or cache is incomplete. Check the model directory for `config.json`, `model.bin` and `tokenizer.json`. An offline lookup cannot download missing weights; a ping alone does not establish model availability.
2. **`cublas64_12.dll not found`**: The process cannot locate CUDA 12 cuBLAS. Check the selected environment, its Torch CUDA build and library search paths using the [GPU runtime](#cuda-runtime) section. A newer driver alone does not supply this DLL.
3. **Whisper model loading segfaults silently**: ctranslate2 version mismatches cuDNN version. Ensure `ctranslate2>=4.5.0` (supports cuDNN 9, which PyTorch 2.6+ ships with).
4. **`RuntimeError: Weights only load failed`**: PyTorch ≥2.6 changed `torch.load` default behavior. Already fixed via monkey-patch in `whisperX_local.py`. If you see this, your code is not up to date.
5. **WhisperX transcription hangs in Streamlit (CPU/GPU idle)**: `librosa.load()` deadlocks in Streamlit's non-main thread. Already fixed by replacing it with `whisperx.audio.load_audio()` (ffmpeg subprocess). If you see this, your code is not up to date.
6. **TorchCodec could not load warning**: This alone does not prevent VideoLingo's WhisperX pipeline from working, because it passes decoded waveforms to pyannote. Run `python installer.py --check` to verify that audio path. Custom code passing filenames to pyannote needs the separate shared-library decoder described [above](#ffmpeg-runtime).
7. **`WhisperX is not installed`**: `whisper.backend` is `whisperx` but the package is not installed. Recognition stops before preparing audio. Install the packages yourself as above, or set `whisper.backend` back to `qwen`. The installer will not install WhisperX for you.
