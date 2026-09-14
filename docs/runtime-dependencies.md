# Runtime dependency refresh

This change retains the existing WhisperX, Streamlit, subtitle and dubbing
architecture. It updates application dependencies within compatible API ranges,
without vendored libraries, package-metadata overrides or a CUDA 13 requirement.

## Installation and updates

`python setup_env.py --shared` creates/reuses the shared environment using Python
3.13. Existing Python 3.10-3.13 environments can run `python installer.py` directly.
Python 3.14 is outside the current WhisperX support range and is rejected before
installation. Recreating an environment with a different Python version requires
confirmation unless `--yes` is supplied.

Use `python installer.py --upgrade` (inside the environment) or
`python setup_env.py --shared --upgrade` to refresh dependencies within the declared
ranges. Normal startup checks do not unconditionally upgrade dependencies.
`OneKeyStart.bat --check-only` reports health without repairing or launching the app.

### Why the GPU stack remains matched

WhisperX 3.8.6 requires Torch/torchaudio 2.8, torchvision 0.23, TorchCodec 0.6-0.7
and huggingface-hub below 1. Transformers 5 requires hub 1 or newer. Consequently,
this refresh retains Transformers 4 and the matched Torch stack rather than
forcing incompatible latest releases.

The installer selects CUDA 12.8 wheels on drivers supporting CUDA 12.8 or newer,
including CUDA 13-capable drivers, and CUDA 12.6 otherwise. CTranslate2's Windows
build needs CUDA 12 cuBLAS. Drivers can be newer than the runtime used by the app.
CPU wheels are explicitly selected on non-NVIDIA Windows/Linux systems.
FFmpeg must be installed separately; TorchCodec requires a shared-library build
for its decoding features. The project itself invokes the FFmpeg CLI.

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

Verified on Windows 11, NVIDIA RTX 4000 Ada (20 GB), Python 3.13.15 and FFmpeg 9.0.1
shared build. The resolved environment has no dependency conflicts (`uv pip check`).
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
