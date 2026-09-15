# Docker installation

## Requirements

Use a Linux NVIDIA GPU host with Docker, a compatible driver and the
[NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).
The host does not need the CUDA Toolkit installed separately for this image.
The driver must support the selected image runtime and the GPU itself.

## Build the checked-out source

Run in a clean public checkout before adding credentials to `config.yaml`.
The Dockerfile copies this checkout, including its configuration, rather than
cloning another revision from GitHub. `.dockerignore` excludes local caches,
outputs and private notes, but does not sanitize a modified configuration file.

```bash
docker build -t videolingo .
```

Default: `nvidia/cuda:12.8.1-cudnn-runtime-ubuntu24.04`, Python 3.13 and PyTorch
cu128. For the matched CUDA 12.6 variant:

```bash
docker build --build-arg CUDA_VERSION=12.6.3 -t videolingo:cu126 .
```

That selects `12.6.3-cudnn-runtime-ubuntu24.04` and cu126 together. No GPU is
required at build time: `setup_env.py` passes an explicit build choice to the
same `installer.py` used on hosts. Other CUDA_VERSION values are rejected.

Both variants use Torch/torchaudio 2.8.0, torchvision 0.23.0 and the same
`requirements.txt` bounds, including WhisperX 3.8, TorchCodec 0.7, Transformers 4
and Hub <1. Demucs 4.1 uses normal dependency resolution. Ubuntu supplies FFmpeg
and its shared libraries, Noto CJK fonts and image runtime libraries.

## Run and preserve data

```bash
docker run -d --name videolingo --gpus all -p 127.0.0.1:8501:8501 -v videolingo-output:/app/output -v videolingo-history:/app/history -v videolingo-models:/app/_model_cache -v videolingo-cache:/app/.cache -v videolingo-hf:/root/.cache/huggingface videolingo
```

Open `http://localhost:8501`. Named volumes preserve output, history and model/ASR
caches when the container is replaced. Mount a local `config.yaml` and
`custom_terms.xlsx` separately if those settings must also persist; the files
must exist before mounting, and configuration needs write access for sidebar edits.
For cu126, use `videolingo:cu126` instead of `videolingo`.

Models are downloaded as needed during processing, not bundled at build time.
Stop the container with `docker stop videolingo`. Port binding above is local-only;
remote access requires an intentionally configured listening address and access controls.

## Verification scope

The Dockerfile runs the shared installation checks and `pip check` during a build.
Source-level checks do not prove a successful image build or GPU processing.
Third-party prebuilt images are not guaranteed to match this checkout's dependencies.
