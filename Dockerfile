ARG CUDA_VERSION=12.4.1
FROM nvidia/cuda:${CUDA_VERSION}-devel-ubuntu20.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ARG PYTHON_VERSION=3.10

# Change software sources and install basic tools and system dependencies
RUN sed -i 's/archive.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    sed -i 's/security.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common git curl sudo ffmpeg fonts-noto wget \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update -y \
    && apt-get install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-dev python${PYTHON_VERSION}-venv \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python${PYTHON_VERSION} 1 \
    && update-alternatives --set python3 /usr/bin/python${PYTHON_VERSION} \
    && ln -sf /usr/bin/python${PYTHON_VERSION}-config /usr/bin/python3-config \
    && curl -sS https://bootstrap.pypa.io/get-pip.py | python${PYTHON_VERSION} \
    && python3 --version && python3 -m pip --version

# Clean apt cache
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Workaround for CUDA compatibility issues
RUN ldconfig /usr/local/cuda-$(echo $CUDA_VERSION | cut -d. -f1,2)/compat/

# Set working directory and clone repository
WORKDIR /app
RUN git clone https://github.com/Huanshere/VideoLingo.git .

# Install PyTorch and torchaudio
RUN pip install torch==2.0.0 torchaudio==2.0.0 --index-url https://download.pytorch.org/whl/cu118

# Clean up unnecessary files
RUN rm -rf .git

# Upgrade pip and install basic dependencies
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# Install dependencies
COPY requirements.txt .
RUN pip install -e .

# Set CUDA-related environment variables
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}

# Set CUDA architecture list
ARG TORCH_CUDA_ARCH_LIST="7.0 7.5 8.0 8.6+PTX"
ENV TORCH_CUDA_ARCH_LIST=${TORCH_CUDA_ARCH_LIST}

EXPOSE 8501

CMD ["streamlit", "run", "st.py"]