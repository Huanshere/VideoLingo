ARG IMAGE_NAME=nvidia/cuda
FROM ${IMAGE_NAME}:12.6.1-runtime-ubuntu24.04 as base

FROM base as base-amd64
ENV NV_CUDNN_VERSION 9.3.0.75-1
ENV NV_CUDNN_PACKAGE_NAME libcudnn9-cuda-12
ENV NV_CUDNN_PACKAGE libcudnn9-cuda-12=${NV_CUDNN_VERSION}

FROM base as base-arm64
ENV NV_CUDNN_VERSION 9.3.0.75-1
ENV NV_CUDNN_PACKAGE_NAME libcudnn9-cuda-12
ENV NV_CUDNN_PACKAGE libcudnn9-cuda-12=${NV_CUDNN_VERSION}

FROM base-${TARGETARCH}

ARG TARGETARCH

LABEL maintainer "NVIDIA CORPORATION <cudatools@nvidia.com>"
LABEL com.nvidia.cudnn.version="${NV_CUDNN_VERSION}"

RUN apt-get update && apt-get install -y --no-install-recommends \
    ${NV_CUDNN_PACKAGE} \
    && apt-mark hold ${NV_CUDNN_PACKAGE_NAME} \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 安装 Python 3.10 和其他系统依赖
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 检查 Python 版本和位置
RUN python3 --version
RUN which python3
RUN ls -l /usr/bin/python*

# 注释掉这些行，暂时不设置 Python 3.10 为默认版本
# RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
# RUN update-alternatives --set python3 /usr/bin/python3.10

# 克隆 VideoLingo 仓库
RUN git clone https://github.com/Huanshere/VideoLingo.git .

# 安装 Python 依赖
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# 安装额外的依赖
RUN pip install --no-cache-dir --break-system-packages streamlit

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES compute,utility

# 暴露 Streamlit 默认端口
EXPOSE 8501

# 启动 Streamlit 应用
CMD ["streamlit", "run", "app.py"]