# 第一阶段：从官方的 PyTorch拉取pytorch
FROM pytorch/pytorch:2.3.1-cuda11.8-cudnn8-runtime AS base

# 设置工作目录
WORKDIR /app

# 第二步：依赖镜像 - 安装 Python 依赖
FROM base AS dependencies

# 设置工作目录
WORKDIR /app

# 安装必要的工具和依赖，并清理缓存
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    cmake \
    build-essential \
    ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 安装基础依赖
RUN pip install --upgrade pip

# 拷贝 requirements.txt 并安装依赖
COPY requirements.txt .
RUN pip install -r requirements.txt

# 第四步：应用镜像
FROM dependencies AS app

# 设置工作目录
WORKDIR /app

# 将当前目录的内容复制到工作目录
COPY . .

# 确保所有脚本是可执行的
RUN chmod +x *.py entrypoint.sh

# 创建并复制 entrypoint.sh 脚本
COPY entrypoint.sh .

# 暴露Streamlit默认端口
EXPOSE 8501

# 启动应用
ENTRYPOINT ["sh", "entrypoint.sh"]
