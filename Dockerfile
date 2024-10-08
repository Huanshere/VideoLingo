# 使用 NVIDIA CUDA 12.4 和 Python 3.10 的基础镜像
FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04

# 设置工作目录
WORKDIR /app

# 安装 Python 3.10 和其他系统依赖
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 设置 Python 3.10 为默认 Python 版本
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
RUN update-alternatives --set python3 /usr/bin/python3.10

# 克隆 VideoLingo 仓库
RUN git clone https://github.com/Huanshere/VideoLingo.git .

# 安装 Python 依赖
RUN pip3 install --no-cache-dir -r requirements.txt

# 安装额外的依赖
RUN pip3 install --no-cache-dir streamlit

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES compute,utility

# 暴露 Streamlit 默认端口
EXPOSE 8501

# 启动 Streamlit 应用
CMD ["streamlit", "run", "app.py"]