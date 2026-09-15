ARG CUDA_VERSION=12.8.1
FROM nvidia/cuda:${CUDA_VERSION}-cudnn-runtime-ubuntu24.04
ARG CUDA_VERSION

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# System Python only bootstraps setup_env.py; the application uses its Python 3.13 venv.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 curl ca-certificates git build-essential ffmpeg fonts-noto-cjk fontconfig libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Build the checked-out source, not a different revision cloned during the build.
WORKDIR /app
COPY . .

# Docker builds normally have no GPU. Keep the wheel family matched to the image.
RUN case "$CUDA_VERSION" in \
        12.8.1) backend=cu128 ;; \
        12.6.3) backend=cu126 ;; \
        *) echo "Use CUDA_VERSION=12.8.1 or 12.6.3" >&2; exit 1 ;; \
    esac \
    && python3 setup_env.py --yes --path /opt/videolingo --torch-backend "$backend" --require-demucs \
    && /opt/videolingo/bin/python -m pip check

ENV PATH="/opt/videolingo/bin:${PATH}"
ENV PYTHONUTF8=1

EXPOSE 8501

CMD ["python", "-m", "streamlit", "run", "st.py", "--server.address=0.0.0.0", "--server.headless=true"]
