# Docker安装

VideoLingo 提供了Dockerfile,可自行使用Dockerfile打包目前VideoLingo。以下是打包和运行的详细说明:

## 系统要求

- CUDA版本 > 12.4
- NVIDIA Driver版本> 550

## 构建和运行Docker镜像或者从DokerHub拉取

```bash
# 构建Docker镜像
docker build -t videolingo .

# 运行Docker容器
docker run -d -p 8501:8501 --gpus all videolingo
```

### 从DockerHub拉取

您可以直接从DockerHub拉取预构建的VideoLingo镜像:

```bash
docker pull rqlove/videolingo:latest
```

拉取完成后,使用以下命令运行容器:

```bash
docker run -d -p 8501:8501 --gpus all rqlove/videolingo:latest
```

注意: 
- `-d` 参数使容器在后台运行
- `-p 8501:8501` 将容器的8501端口映射到主机的8501端口
- `--gpus all` 启用所有可用的GPU支持
- 确保使用完整的镜像名称 `rqlove/videolingo:latest`

## 模型

whisper 模型不包含在镜像中,会在容器首次运行时自动下载。如果您希望跳过自动下载过程,可以从以下链接下载模型权重:

- [Google Drive链接](https://drive.google.com/file/d/10gPu6qqv92WbmIMo1iJCqQxhbd1ctyVw/view?usp=drive_link)
- [百度网盘链接](https://pan.baidu.com/s/1hZjqSGVn3z_WSg41-6hCqA?pwd=2kgs)

下载后,使用以下命令运行容器,将模型文件挂载到容器中:

```bash
docker run -d -p 8501:8501 --gpus all -v /path/to/your/model:/app/_model_cache rqlove/videolingo:latest
```

请注意将 `/path/to/your/model` 替换为您实际下载模型文件的本地路径。

## 其他说明

- 基础镜像: nvidia/cuda:12.4.1-devel-ubuntu20.04
- Python版本: 3.10
- 预装软件: git, curl, sudo, ffmpeg, fonts-noto等
- PyTorch版本: 2.0.0 (CUDA 11.8)
- 暴露端口: 8501 (Streamlit应用)

如需更多详细信息,请参考Dockerfile。

