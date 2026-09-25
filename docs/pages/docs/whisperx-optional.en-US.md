# WhisperX (optional)

VideoLingo's default local speech recognition is **Qwen3-ASR + Qwen3-ForcedAligner**; see the [Start guide](start.en-US.md#asr-runtime). WhisperX remains available as an optional fallback: its code path and behavior are unchanged (including the forced Belle model for Chinese), but **the default installation no longer includes WhisperX**, and `installer.py` neither installs nor requires it.

Consider WhisperX when you want to compare against Qwen, want the punctuation-enhanced Belle Whisper model for Chinese, or already rely on a WhisperX-based workflow.

## Support

| Platform | Same environment as the default? | Notes |
|:---------|:---------------------------------|:------|
| Windows / Linux | Yes | Add it to the VideoLingo environment as shown below. Dependency resolution was verified with `uv pip compile` (Python 3.13); recognition has not been run in this repository's test environment |
| Apple Silicon Mac | **No** | The default MLX backend needs `huggingface-hub>=1`; WhisperX 3.8.6 needs `huggingface-hub<1`. Create a **separate environment** for WhisperX instead of installing it into the default one |

## Install

Run this inside the VideoLingo environment created by `setup_env.py` (the project `.venv` is shown; for a `--shared` environment use `~/.venvs/videolingo`):

```bash
# Windows
.venv\Scripts\python -m pip install "whisperx>=3.8.6,<3.9" "ctranslate2>=4.5,<5" "pyannote-audio>=4.0.4,<5" "torchcodec>=0.7,<0.8"
# Linux
.venv/bin/python -m pip install "whisperx>=3.8.6,<3.9" "ctranslate2>=4.5,<5" "pyannote-audio>=4.0.4,<5" "torchcodec>=0.7,<0.8"
```

These are the same constraints `requirements.txt` used in 3.0.4. WhisperX 3.8 needs Torch/torchaudio 2.8, torchvision 0.23 and Transformers 4, which match the default environment, so the installed PyTorch build does not change.

Then run `python installer.py --check`. When whisperx is installed, the check also probes whether TorchCodec can load the FFmpeg shared libraries; without whisperx this probe is skipped. On Windows/Linux, rerunning `installer.py` or `--upgrade` does not uninstall WhisperX; if the check reports a problem, rerun the install command above. On Apple Silicon, rerunning `installer.py` actively uninstalls the WhisperX stack (whisperx, torchcodec, faster-whisper, ctranslate2, pyannote-*) from the default environment (see below).

## Enable

In the sidebar choose "ASR Runtime: Local" → "Local ASR Backend: WhisperX (optional fallback)", or set in `config.yaml`:

```yaml
whisper:
  runtime: 'local'
  backend: 'whisperx'
  model: 'large-v3'   # or large-v3-turbo; WhisperX only
  language: 'en'
```

- With recognition language `zh`, the WhisperX path forces `Huan69/Belle-whisper-large-v3-zh-punct-fasterwhisper` and ignores `whisper.model`.
- If Chinese is detected while the recognition language is not `zh`, the WhisperX path stops and asks you to select Chinese explicitly.
- The transcription cache key includes the backend, so WhisperX and Qwen results are never reused for each other.

<a id="cuda-runtime"></a>
## GPU runtime (CUDA 12 cuBLAS / cuDNN 9)

The default Qwen path only needs the CUDA runtime bundled with PyTorch. WhisperX uses CTranslate2 (faster-whisper), whose GPU execution also needs **CUDA 12 cuBLAS and cuDNN 9** accessible to the process. See [faster-whisper's GPU requirements](https://github.com/SYSTRAN/faster-whisper#gpu) and [CTranslate2 4.5's cuDNN 9 transition](https://github.com/OpenNMT/CTranslate2/releases/tag/v4.5.0).

- If the libraries are missing on Windows, obtain CUDA 12 libraries from NVIDIA's [CUDA 12.8 Update 1 archive](https://developer.nvidia.com/cuda-12-8-1-download-archive) and cuDNN 9 **for CUDA 12** from [NVIDIA](https://developer.nvidia.com/cudnn-downloads). Add the actual DLL directories to PATH and reopen the terminal. Do not invent a cuDNN directory by substituting the PyTorch build tag into an example path.
- On Linux, follow faster-whisper's linked instructions for exposing the installed cuBLAS/cuDNN libraries through `LD_LIBRARY_PATH` before starting Python. The Docker image is based on `cudnn-runtime` and includes these libraries.

<a id="ffmpeg-runtime"></a>
## FFmpeg shared libraries (TorchCodec 0.7)

The WhisperX chain (pyannote) loads FFmpeg **shared libraries** through TorchCodec; the FFmpeg CLI alone is not enough. The pinned TorchCodec 0.7 supports FFmpeg 4–7, not FFmpeg 8/9. Use a shared FFmpeg 7 build.

On Windows, this [BtbN 7.1 shared build](https://github.com/BtbN/FFmpeg-Builds/releases/download/autobuild-2025-07-31-14-15/ffmpeg-n7.1.1-56-gc2184b65d2-win64-gpl-shared-7.1.zip)
was downloaded and verified with real audio decoding. Extract it and put its `bin` directory ahead of other FFmpeg versions on PATH. VideoLingo registers that directory for Windows DLL loading. Package managers may supply newer incompatible FFmpeg libraries, so check the version rather than assuming latest works.

## Apple Silicon: use a separate environment

On Apple Silicon the default requirements install mlx-audio (Transformers 5, `huggingface-hub>=1`), while WhisperX 3.8.6 requires `huggingface-hub<1`, so they cannot share one environment. `uv` only resolves the combination by picking the pre-release whisperx 3.8.7rc1, which is unverified and not recommended.

To use WhisperX on a Mac, create a separate virtual environment for it; do not run the install command above in the default environment. This repository does not ship an installer for that separate environment, and the combination has not been verified. If the default environment already has whisperx (for example after upgrading from an older version), rerunning `installer.py` first uninstalls the WhisperX stack (whisperx, torchcodec, faster-whisper, ctranslate2, pyannote-*) (packages that another installed package still requires are kept), and `installer.py --check` reports the combination as an error.

<a id="common-errors"></a>
## Common errors

1. **`local_files_only=True`**: The selected local Whisper model or cache is incomplete. Check the model directory for `config.json`, `model.bin` and `tokenizer.json`. An offline lookup cannot download missing weights; a ping alone does not establish model availability.
2. **`cublas64_12.dll not found`**: The process cannot locate CUDA 12 cuBLAS. Check the selected environment, its Torch CUDA build and library search paths using the [GPU runtime](#cuda-runtime) section. A newer driver alone does not supply this DLL.
3. **Whisper model loading segfaults silently**: ctranslate2 version mismatches cuDNN version. Ensure `ctranslate2>=4.5.0` (supports cuDNN 9, which PyTorch 2.6+ ships with).
4. **`RuntimeError: Weights only load failed`**: PyTorch ≥2.6 changed `torch.load` default behavior. Already fixed via monkey-patch in `whisperX_local.py`. If you see this, your code is not up to date.
5. **WhisperX transcription hangs in Streamlit (CPU/GPU idle)**: `librosa.load()` deadlocks in Streamlit's non-main thread. Already fixed by replacing it with `whisperx.audio.load_audio()` (ffmpeg subprocess). If you see this, your code is not up to date.
6. **TorchCodec could not load**: The TorchCodec probe in `installer.py --check` failed, usually because FFmpeg is 8/9 or only the CLI is installed without shared libraries. See [FFmpeg shared libraries](#ffmpeg-runtime).
7. **`No module named 'whisperx'`**: The WhisperX backend is selected but not installed. Install it as above, or switch back to Qwen3-ASR in the sidebar.
