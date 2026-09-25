# Runtime dependency refresh

> BUILDER-305 update: the default local ASR is now Qwen3-ASR + Qwen3-ForcedAligner
> and WhisperX is optional (not in `requirements.txt`). See "Default ASR
> dependencies" below; the WhisperX notes in the rest of this page describe the
> #599 refresh and now apply only when WhisperX is installed.

This change retains the existing WhisperX, Streamlit, subtitle and dubbing
architecture. It updates application dependencies within compatible API ranges,
without vendored libraries, package-metadata overrides or a CUDA 13 requirement.

## Installation and updates

`python setup_env.py --shared` creates/reuses the shared environment using Python
3.13. Existing Python 3.10-3.13 environments can run `python installer.py` directly.
Python 3.14 is outside the supported range and is rejected before installation. Recreating an environment with a different Python version requires
confirmation unless `--yes` is supplied.

Use `python installer.py --upgrade` (inside the environment) or
`python setup_env.py --shared --upgrade` to refresh dependencies within the declared
ranges. Normal startup checks do not unconditionally upgrade dependencies.
`OneKeyStart.bat --check-only` reports health without repairing or launching the app.

### Why the GPU stack remains matched (#599; WhisperX only)

This section records the #599 policy for the WhisperX stack. Since BUILDER-305 it
applies only when the optional WhisperX fallback is installed on Windows/Linux; the
default Qwen3-ASR stack uses Transformers 5 on Apple Silicon (see below).

WhisperX 3.8.6 requires Torch/torchaudio 2.8, torchvision 0.23, TorchCodec 0.6-0.7
and huggingface-hub below 1. Transformers 5 requires hub 1 or newer. Consequently,
this refresh retains Transformers 4 and the matched Torch stack rather than
forcing incompatible latest releases.

The installer selects CUDA 12.8 wheels on drivers supporting CUDA 12.8 or newer,
including CUDA 13-capable drivers, and CUDA 12.6 otherwise. With WhisperX installed,
CTranslate2's Windows build also needs CUDA 12 cuBLAS. Drivers can be newer than the runtime used by the app.
CPU wheels are explicitly selected on non-NVIDIA Windows/Linux systems.
FFmpeg must be installed separately. The pinned TorchCodec 0.7 build needs
FFmpeg 4–7 shared libraries; FFmpeg 8/9 are not supported. On Windows use the
[FFmpeg 7 shared build documented in the WhisperX guide](pages/docs/whisperx-optional.en-US.md#ffmpeg-runtime).
The project invokes the FFmpeg CLI, and `installer.py` probes TorchCodec at
install/check time because package metadata can pass while decoding fails.

### Default ASR dependencies (BUILDER-305)

`requirements.txt` selects the Qwen3-ASR engine with environment markers:

| Platform | Packages | Transformers / Hub |
| --- | --- | --- |
| Apple Silicon (`darwin` + `arm64`) | `mlx-audio>=0.5.5,<0.6`, plus `nagisa==0.2.11` and `soynlp==0.0.493` | `transformers>=5.14,<6`, `huggingface-hub>=1,<2` |
| Windows and Linux | `qwen-asr==0.0.6` | `transformers>=4.57.6,<5`, `huggingface-hub>=0.36.2,<1` |

The non-Apple-Silicon marker also matches Intel Macs, but PyTorch 2.8 has no macOS
x86_64 wheels, so `installer.py` stops there before running pip. It also stops on
Apple Silicon below macOS 14, where mlx has no wheels. On Apple Silicon the
installer uninstalls the WhisperX stack (whisperx, torchcodec, faster-whisper, ctranslate2, pyannote-*) before syncing requirements,
because WhisperX 3.8's `huggingface-hub<1` conflicts with mlx-audio's `>=1`.

Why the split: every mlx-audio release that includes Qwen3-ASR requires
Transformers 5, and 0.4.2+ also requires huggingface-hub 1. qwen-asr 0.0.6 pins
`transformers==4.57.6` and `accelerate==1.12.0` exactly (and pulls in gradio and
flask), so Transformers stays on 4.x wherever qwen-asr is used. mlx only publishes
macOS ≥14 arm64 wheels, so Apple Silicon needs macOS 14 or newer. mlx-audio's
forced aligner imports nagisa (Japanese) and soynlp (Korean) lazily without
declaring them, so they are listed explicitly with qwen-asr's pins.

WhisperX, pyannote-audio, CTranslate2 and TorchCodec are no longer default
requirements. `huggingface-hub<1`, TorchCodec 0.7 and the FFmpeg 4–7 shared-library
requirement only matter when WhisperX is installed; `installer.py --check` runs the
TorchCodec probe only in that case. The default path decodes audio with the FFmpeg
CLI. Install steps for WhisperX are in
[WhisperX (optional)](pages/docs/whisperx-optional.en-US.md); on Apple Silicon
stable WhisperX 3.8.6 (hub <1) cannot share the MLX environment (hub ≥1).

Verified offline (`uv pip compile`, Python 3.13, 2026-09-24):

- Linux x86_64 and Windows x86_64: qwen-asr 0.0.6, transformers 4.57.6,
  huggingface-hub 0.36.2, accelerate 1.12.0, torch 2.8.0.
- macOS arm64 with `MACOSX_DEPLOYMENT_TARGET=14.0`: mlx-audio 0.5.5, mlx 0.32.2,
  transformers 5.17.0, huggingface-hub 1.33.0, nagisa 0.2.11, soynlp 0.0.493.
  The default macOS 13 target fails because mlx has no wheel for it.
- Linux/Windows defaults plus the four WhisperX packages resolve (whisperx 3.8.6,
  torchcodec 0.7.0, pyannote-audio 4.0.7, transformers 4.57.6, hub 0.36.2). On
  macOS arm64, uv only resolves by selecting the pre-release whisperx 3.8.7rc1.

Not verified: installing these environments and running Qwen3-ASR inference
(transformers on CUDA/CPU, MLX on Apple Silicon), GPU memory use and speed, and
the Docker image build with the new requirements.

### Reduced installation complexity

- Remove unused MoviePy and Replicate dependencies.
- Remove the direct resampy requirement; remaining libraries manage their own
  transitive dependencies.
- Let pyannote-audio/WhisperX resolve Lightning instead of separately pinning
  both Lightning distributions.
- Use maintained PyPI Demucs 4.1 instead of a Git development snapshot and
  `--no-deps` workaround. Training extras are not needed for inference.
- Import Demucs only when separation is requested by the transcription stage.
- Use one FFmpeg WAV slicing helper for the two cloud ASR backends instead of
  decoding the entire audio through librosa and re-encoding separately.
- Launch Edge TTS with the active Python interpreter, not a possibly unrelated
  executable on the system PATH.

## Validation

Run `python -m pytest tests/test_dependencies.py` for targeted regression checks.
The suite requires the app dependencies, pytest and FFmpeg.

`tests/test_pipeline_integration.py` is explicitly opt-in and spends API credits.
Set `VIDEOLINGO_TEST_AUDIO` to an English WAV and `VIDEOLINGO_TEST_API_KEY` to a
valid OpenAI-compatible key. Optionally set `VIDEOLINGO_TEST_BASE_URL` and
`VIDEOLINGO_TEST_MODEL`. It tests real translation, subtitle burn-in and Edge TTS
dubbing through the existing background TaskRunner, plus audio-only subtitles.
Generated outputs use pytest temporary directories and the temporary credential
configuration is removed at teardown.

#599 recorded a Windows 11, NVIDIA RTX 4000 Ada (20 GB), Python 3.13.15
environment with FFmpeg 9.0.1 shared libraries and a complete translation/dubbing
pipeline. That FFmpeg 9.0.1 note is superseded: later TorchCodec 0.7 runtime
probing showed FFmpeg 9 can fail to load even when `pip check` is clean.
Current requirement is TorchCodec 0.7 with FFmpeg 4–7 shared libraries
(FFmpeg 7 on Windows). See `docs/deployment-versions.md` for that follow-up.
The #599 resolved environment had no dependency conflicts (`uv pip check`).
Representative versions: WhisperX 3.8.6, Torch 2.8.0+cu128, CTranslate2 4.8.2,
pyannote-audio 4.0.7, TorchCodec 0.7.0, spaCy 3.8.16, Streamlit 1.63.0,
pandas 3.0.5, NumPy 2.5.3, OpenAI client 3.13.0 and Demucs 4.1.0.

Real integration uses a roughly 15-second public English speech sample,
OpenLux's OpenAI-compatible endpoint with gpt-5.5 for Simplified Chinese
translation, and Edge TTS for Chinese dubbing. It checks generated subtitle,
audio and video artifacts, not subjective translation or dubbing quality.
The public sample is available at
https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen3-ASR-Repo/asr_en.wav.
With `VIDEOLINGO_TEST_SERVER=1` and the integration variables supplied, the final
suite passed all 15 checks, including a real HTTP/WebSocket first-page render.

Not claimed as live-verified: Linux/macOS runtime, other ASR languages, YouTube
availability, paid 302.ai/ElevenLabs/other TTS accounts, or GPT-SoVITS services.
Cloud ASR slicing is tested locally without claiming successful cloud requests.
