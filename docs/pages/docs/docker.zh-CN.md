# Docker安装

VideoLingo 提供了Dockerfile,可自行使用Dockerfile打包目前VideoLingo。以下是打包和运行的详细说明:

## 系统要求

- CUDA版本 > 12.4
- NVIDIA Driver版本> 550

## 构建和运行Docker镜像

```bash
# 构建Docker镜像
docker build -t videolingo .

# 运行Docker容器
docker run -d -p 8501:8501 --gpus all videolingo
```

注意: 运行容器时需要添加`--gpus all`参数以启用GPU支持。

## 模型

VideoLingo Docker 镜像中已经包含了以下模型:

- UVR模型:
  - HP2_all_vocals.pth
  - VR-DeEchoAggressive.pth

whisper模型不包含在镜像中,会在容器首次运行时自动下载。

## 其他说明

- 基础镜像: nvidia/cuda:12.4.1-devel-ubuntu20.04
- Python版本: 3.10
- 预装软件: git, curl, sudo, ffmpeg, fonts-noto等
- PyTorch版本: 2.0.0 (CUDA 11.8)
- 默认语言设置: 英语 (en_US)
- 暴露端口: 8501 (Streamlit应用)

如需更多详细信息,请参考Dockerfile。

## 后续规划

- 继续完善Dockerfile，减少镜像体积
- 将docker镜像推送到docker hub
- 所需模型支持使用-v参数挂载到宿主机
