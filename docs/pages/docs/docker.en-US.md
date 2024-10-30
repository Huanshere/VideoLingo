# Docker Installation

VideoLingo provides a Dockerfile that you can use to build the current VideoLingo package. Here are detailed instructions for building and running:

## System Requirements

- CUDA version > 12.4
- NVIDIA Driver version > 550

## Building and Running the Docker Image or Pulling from DockerHub

```bash
# Build the Docker image
docker build -t videolingo .

# Run the Docker container
docker run -d -p 8501:8501 --gpus all videolingo
```

### Pulling from DockerHub

You can directly pull the pre-built VideoLingo image from DockerHub:

```bash
docker pull rqlove/videolingo:latest
```

After pulling, use the following command to run the container:

```bash
docker run -d -p 8501:8501 --gpus all rqlove/videolingo:latest
```

Note: 
- The `-d` parameter runs the container in the background
- `-p 8501:8501` maps port 8501 of the container to port 8501 of the host
- `--gpus all` enables support for all available GPUs
- Make sure to use the full image name `rqlove/videolingo:latest`

## Models

The Whisper model is not included in the image and will be automatically downloaded when the container is first run. If you want to skip the automatic download process, you can download the model weights from [here](https://drive.google.com/file/d/10gPu6qqv92WbmIMo1iJCqQxhbd1ctyVw/view?usp=drive_link) or [Baidu Netdisk](https://pan.baidu.com/s/1hZjqSGVn3z_WSg41-6hCqA?pwd=2kgs) (Passcode: 2kgs).

After downloading, use the following command to run the container, mounting the model file into the container:

```bash
docker run -d -p 8501:8501 --gpus all -v /path/to/your/model:/app/_model_cache rqlove/videolingo:latest
```

Please replace `/path/to/your/model` with the actual local path where you downloaded the model file.

## Additional Information

- Base image: nvidia/cuda:12.4.1-devel-ubuntu20.04
- Python version: 3.10
- Pre-installed software: git, curl, sudo, ffmpeg, fonts-noto, etc.
- PyTorch version: 2.0.0 (CUDA 11.8)
- Exposed port: 8501 (Streamlit application)

For more detailed information, please refer to the Dockerfile.

## Future Plans

- Continue to improve the Dockerfile to reduce image size
- Push the Docker image to Docker Hub
- Support mounting required models to the host machine using the -v parameter
