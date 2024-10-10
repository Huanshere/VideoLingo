# Docker Installation

VideoLingo provides a Dockerfile that you can use to build the current VideoLingo package. Here are detailed instructions for building and running:

## System Requirements

- CUDA version > 12.4
- NVIDIA Driver version > 550

## Building and Running the Docker Image

```bash
# Build the Docker image
docker build -t videolingo .

# Run the Docker container
docker run -d -p 8501:8501 --gpus all videolingo
```

Note: Add the `--gpus all` parameter when running the container to enable GPU support.

## Models

The VideoLingo Docker image includes the following models:

- UVR models:
  - HP2_all_vocals.pth
  - VR-DeEchoAggressive.pth

The Whisper model is not included in the image and will be automatically downloaded when the container is first run.

## Additional Information

- Base image: nvidia/cuda:12.4.1-devel-ubuntu20.04
- Python version: 3.10
- Pre-installed software: git, curl, sudo, ffmpeg, fonts-noto, etc.
- PyTorch version: 2.0.0 (CUDA 11.8)
- Default language setting: English (en_US)
- Exposed port: 8501 (Streamlit application)

For more detailed information, please refer to the Dockerfile.

## Future Plans

- Continue to improve the Dockerfile to reduce image size
- Push the Docker image to Docker Hub
- Support mounting required models to the host machine using the -v parameter

```

