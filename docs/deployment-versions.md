# Deployment dependency audit

Reviewed against upstream `c5f8fe7` on 2026-09-15. Git trees, not PR descriptions
or commit timestamps alone, determine the effective dependency versions.

## History

| Baseline/change | Effective dependency changes |
| --- | --- |
| `v2.2.1` | NVIDIA: Torch/torchaudio 2.0.0 from cu118; CPU: 2.1.2. WhisperX Git revision `7307306`, Demucs Git development extra, CTranslate2 4.4.0, NumPy 1.26.4, Transformers 4.39.3, spaCy 3.7.4, Streamlit 1.38.0, librosa 0.10.2.post1. |
| `v3.0.0` | Retains that dependency family; adds xmltodict. The Dockerfile independently pins Torch 2.0.0/cu118. |
| #531, included in `v3.0.1` | Intermediate Torch 2.6/cu124 and WhisperX 3.4 work is superseded within the PR by Torch 2.8, WhisperX >=3.8.1, pyannote-audio >=4, CTranslate2 >=4.5/cuDNN 9, NumPy >=2, librosa 0.11, spaCy 3.8.11, Streamlit 1.49.1 and Lightning 2.6.1. Demucs installed separately with --no-deps. Docker documentation changed but Dockerfile did not. |
| `301d561`, also ancestor of `v3.0.1` | Adds cu129 to the old install.py selection. This is historical, not a pending future change. |
| #537 | Adds uv/Python 3.10 setup and project-venv batch launcher; dependency installation remains in install.py. |
| #576/#577 | Shared/local environments, staged installer.py, legacy install.py wrapper, bounded spaCy 3.8, separate WhisperX/Demucs stages. Docker and Colab were not migrated. |
| #599 | New uv environments use Python 3.13; existing environments supported on 3.10–3.13. Torch/torchaudio 2.8.0, torchvision 0.23.0, WhisperX >=3.8.6,<3.9, TorchCodec >=0.7,<0.8, Transformers <5, Hub <1. Normal PyPI Demucs >=4.1,<5 replaces Git/--no-deps. CUDA selection becomes cu128/cu126, CPU index explicit. Removes MoviePy, Replicate, direct resampy and duplicate Lightning pins. |
| #602/#610/#611 | Runtime/cache/logging and audio-processing changes; no replacement of the #599 dependency family. Audio sample rates and bitrates are media settings, not CUDA dependency versions. |

Full current application bounds are in `requirements.txt`; optional Demucs is in
`installer.py`. Do not copy an older PR's intermediate version list into setup.

## Deployment alignment

- Host uv setup: `setup_env.py` creates Python 3.13 and delegates to `installer.py`.
  Auto selection uses the driver's `nvidia-smi` CUDA capability: >=12.8 selects
  cu128, otherwise cu126 when NVIDIA is detected. An unparseable capability also
  falls back to cu126; this fallback is not a compatibility guarantee. No NVIDIA
  selects CPU. Existing compatible builds can be reused without replacement.
- Docker: CUDA 12.8.1/cuDNN runtime on Ubuntu 24.04, Python 3.13 through the same
  setup script, explicit cu128. `CUDA_VERSION=12.6.3` selects the matching cu126
  variant. Explicit selection is necessary because image builds normally cannot
  see the runtime GPU. Host driver and NVIDIA Container Toolkit remain external.
  Source comes from the build context, not a fresh upstream clone. Build performs
  the common installer check and pip check; no model is downloaded at build time.
- Colab: application runs from its own Python 3.13 venv and the same installer.
  Colab's kernel Python remains platform-managed; pyngrok runs there. The install
  cell does not launch Streamlit, and the final cell uses the application venv.
  Embedded output logs predate this change and are explicitly labeled historical.
- Windows batch: shared venv, project venv, then existing legacy environment, with
  the common version check. The uv-named entry point delegates to the same launcher.
- Existing `install.py` delegates to `installer.py`; it is a compatibility wrapper,
  not another version policy. Direct `pip install -e .` uses requirements.txt but
  does not select GPU wheels or install optional Demucs. Use the staged installer.

CUDA Toolkit, PyTorch build tags and the driver's CUDA capability are different
layers. The installer selects Python wheels; it does not install a system Toolkit.
CUDA 13-capable drivers may run CUDA 12 builds. CTranslate2 4.5's release explicitly
migrates to cuDNN 9; its generic installation page still mentions cuDNN 8, so use
the release-specific requirement and faster-whisper's current GPU instructions.

## Verification boundary

Actual validation on 2026-09-15:

- Linux amd64, Docker Engine 24.0.2: default CUDA 12.8.1 image built successfully
  (`7471025af15a`, approximately 19 GB). Build-time and separate container
  `pip check` passed. Imported Torch/torchaudio 2.8.0+cu128, torchvision
  0.23.0+cu128, WhisperX ASR, TorchCodec 0.7.0, CTranslate2 4.8.2, Demucs API,
  Streamlit, spaCy 3.8.16, librosa 1.0.0 and OpenCV 5.0.0.
- In that image, FFmpeg generated a one-second WAV and TorchCodec decoded all
  44,100 samples. FFmpeg also rendered text using the installed Noto CJK font.
- Actual execution exposed a false font warning: `fc-match` needs the family
  `Noto Sans CJK SC`, not the filename stem `NotoSansCJK-Regular`. The corrected
  installer was mounted into the built image and its full environment check
  passed without that warning. The full image was not rebuilt after this fix.
- Windows driver 610.88 reports `CUDA UMD Version: 13.3`. Detection now accepts
  that format as well as `CUDA Version`, rather than silently selecting cu126.
- Windows fresh Python 3.13 environment completed installation including Demucs
  4.1.0; pip check passed. CUDA matrix multiplication on an RTX 4000 Ada passed,
  and CTranslate2 detected one CUDA device. Initial TorchCodec import failed with
  system FFmpeg 9.0.1. A downloaded BtbN FFmpeg 7.1 shared build plus explicit
  Windows DLL-directory registration fixed it; all major imports and decoding
  a one-second WAV to 44,100 samples passed. The installer now probes TorchCodec
  in a subprocess and rejects the incompatible FFmpeg 9 environment instead of
  reporting metadata-only success. `runtime_libraries.py` also configures DLL
  lookup before the application's core imports. These final changes were verified
  on Windows, not included in the earlier Docker image build.
- Twenty focused mocked installer tests passed, with six unrelated tests excluded.
  Python syntax, notebook JSON/code and seven-language README commands also passed.

The Docker host has no NVIDIA GPU: this verifies the CUDA image can be built on
a GPU-less host, not GPU inference. The cu126 image variant and an actual Colab
session have not been run. Component import and media decoding are not a complete
translation/dubbing quality test. Production environments and services are preserved.
