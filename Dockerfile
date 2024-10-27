# Define base image with specified CUDA version
ARG CUDA_VERSION=12.4.1
FROM nvidia/cuda:${CUDA_VERSION}-devel-ubuntu20.04

# Set environment variables and Python version
ENV DEBIAN_FRONTEND=noninteractive \
    CUDA_HOME=/usr/local/cuda
ARG PYTHON_VERSION=3.10

# Update apt sources, install dependencies, and set up Python
RUN sed -i 's/archive.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    sed -i 's/security.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common git curl sudo ffmpeg fonts-noto wget && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-dev python${PYTHON_VERSION}-venv && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python${PYTHON_VERSION} 1 && \
    update-alternatives --set python3 /usr/bin/python${PYTHON_VERSION} && \
    ln -sf /usr/bin/python${PYTHON_VERSION}-config /usr/bin/python3-config && \
    curl -sS https://bootstrap.pypa.io/get-pip.py | python${PYTHON_VERSION} && \
    python3 --version && python3 -m pip --version && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Configure CUDA compatibility
RUN ldconfig /usr/local/cuda-$(echo $CUDA_VERSION | cut -d. -f1,2)/compat/

# Set up working directory and clone repository
WORKDIR /app
RUN git clone https://github.com/Huanshere/VideoLingo.git .

# Install PyTorch and torchaudio
RUN pip install torch==2.0.0 torchaudio==2.0.0 --index-url https://download.pytorch.org/whl/cu118

# Clean up unnecessary files
RUN rm -rf .git

# Upgrade pip and install core dependencies
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --no-cache-dir --upgrade pip requests rich ruamel.yaml

# Install WhisperX and additional dependencies
RUN cd third_party/whisperX && pip install --no-cache-dir -e .
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download UVR models with error handling for reliability
RUN mkdir -p _model_cache/uvr5_weights && \
    wget -q -O _model_cache/uvr5_weights/HP2_all_vocals.pth https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/e992cb1bc5d777fcddce20735a899219b1d46aba/uvr5_weights/HP2_all_vocals.pth || echo "Download failed for HP2_all_vocals.pth" && \
    wget -q -O _model_cache/uvr5_weights/VR-DeEchoAggressive.pth https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/uvr5_weights/VR-DeEchoAggressive.pth || echo "Download failed for VR-DeEchoAggressive.pth"

# Set PATH and library path for CUDA
ENV PATH=${CUDA_HOME}/bin:${PATH} \
    LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH} \
    TORCH_CUDA_ARCH_LIST="7.0 7.5 8.0 8.6+PTX"

# Expose application port
EXPOSE 8501

# Start the application
CMD ["streamlit", "run", "st.py"]
