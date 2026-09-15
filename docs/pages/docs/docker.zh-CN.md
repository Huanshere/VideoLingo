# Docker 安装

## 环境要求

使用 Linux NVIDIA GPU 主机，安装 Docker、兼容的显卡驱动和
[NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)。
本镜像不要求主机另外安装 CUDA Toolkit，驱动需支持所选镜像运行库和显卡本身。

## 构建当前代码

在填写 `config.yaml` 凭据之前，从干净的公开代码目录构建。
Dockerfile 复制当前目录及配置，不会另行从 GitHub 克隆不同版本。
`.dockerignore` 排除本地缓存、输出和私人笔记，但不会清除已修改配置里的凭据。

```bash
docker build -t videolingo .
```

默认使用 `nvidia/cuda:12.8.1-cudnn-runtime-ubuntu24.04`、Python 3.13 和 PyTorch
cu128。匹配的 CUDA 12.6 方案：

```bash
docker build --build-arg CUDA_VERSION=12.6.3 -t videolingo:cu126 .
```

这会同时选择 `12.6.3-cudnn-runtime-ubuntu24.04` 和 cu126。构建时不需要 GPU：
`setup_env.py` 把明确的构建选择传给与主机共用的 `installer.py`。
其他 CUDA_VERSION 值会被拒绝。

两个方案均采用 Torch/torchaudio 2.8.0、torchvision 0.23.0 和相同的
`requirements.txt` 约束，包括 WhisperX 3.8、TorchCodec 0.7、Transformers 4、
Hub <1。Demucs 4.1 使用正常依赖解析。Ubuntu 提供 FFmpeg 及共享库、Noto CJK
字体和图像运行库。

## 启动并保留数据

```bash
docker run -d --name videolingo --gpus all -p 127.0.0.1:8501:8501 -v videolingo-output:/app/output -v videolingo-history:/app/history -v videolingo-models:/app/_model_cache -v videolingo-cache:/app/.cache -v videolingo-hf:/root/.cache/huggingface videolingo
```

打开 `http://localhost:8501`。命名卷让输出、历史和模型/识别缓存在替换容器后保留。
如需保留配置和术语表，另行挂载本地 `config.yaml` 和 `custom_terms.xlsx`。
挂载前文件必须存在，侧栏修改配置需要写权限。使用 cu126 时，将镜像名替换为
`videolingo:cu126`。

模型在处理时按需下载，不包含在构建镜像内。执行 `docker stop videolingo` 停止。
上述端口仅监听本机，远程访问需要明确配置监听地址及访问控制。

## 验证范围

Dockerfile 在构建时执行共用安装检查和 `pip check`。源码检查不等于已经成功构建
镜像或完成 GPU 处理。第三方预构建镜像不保证与当前代码的依赖一致。
