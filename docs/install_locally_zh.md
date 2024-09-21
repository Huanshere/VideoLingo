# 🏠 VideoLingo 安装指南

## Whisper 模型选择
VideoLingo 使用 WhisperX 进行语音识别，支持本地部署和云端api

| 方案 | 缺点 |
|:-----|:-----|
| **whisperX 🖥️** | • 安装CUDA 🛠️<br>• 下载模型 📥<br>• 高显存 💾 |
| **whisperX ☁️** | • 需梯子 🕵️‍♂️<br>• Visa卡 💳 |

## 📋 API 准备

1. **获取大模型的 API_KEY**：

| 模型 | 推荐提供商 | base_url | 价格 | 效果 |
|:-----|:---------|:---------|:-----|:---------|
| claude-3-5-sonnet-20240620 | [ 云雾 api](https://yunwu.zeabur.app/register?aff=TXMB) | https://yunwu.zeabur.app | ￥15 / 1M | 🤩 |
| Qwen/Qwen2.5-72B-Instruct | [硅基流动](https://cloud.siliconflow.cn/i/ttKDEsxE) | https://api.siliconflow.cn | ￥4 / 1M | 😲 |

### 常见问题

<details>
<summary>如何选择模型？</summary>

- 🚀 默认使用Qwen2.5, 1h 视频翻译花费约 ￥3。
- 🌟 Claude 3.5 效果更好，翻译的连贯性非常好，且没有 ai 味，但价格更贵。
</details>

<details>
<summary>如何获取 api key？</summary>

1. 在任何一家大模型提供商进行注册
2. 充值账户
3. 在 api key 页面新建一个即可
</details>

<details>
<summary>能用别的模型吗？</summary>

- ✅ 支持 OAI-Like 的 API 接口，需要自行在 streamlit 侧边栏更换。
- ⚠️ 但其余模型遵循指令要求能力弱，非常容易在翻译过程报错，强烈不推荐。
</details>

2. **准备 Replicate 的 Token** （仅当使用 whisperX ☁️ 时）
   - 在 [Replicate](https://replicate.com/account/api-tokens) 注册并绑定 Visa 卡支付方式，获取令牌
   - 或加入 QQ 群在群公告中免费获取测试令牌

## 🚀 whisperX ☁️ 整合包

1. 下载 `v0.8.2` 一键整合包(700M): [直达链接](https://vip.123pan.cn/1817874751/8101255) | [度盘备用](https://pan.baidu.com/s/1H_3PthZ3R3NsjS0vrymimg?pwd=ra64)

2. 解压后双击运行文件夹中的 `一键启动.bat`

3. 在打开的浏览器窗口中，在侧边栏进行必要配置，然后一键出片！
  ![settings](https://github.com/user-attachments/assets/3d99cf63-ab89-404c-ae61-5a8a3b27d840)

## 🛠️ 源码安装流程

### Windows 前置依赖

在开始安装 VideoLingo 之前，注意预留至少 **20G** 硬盘空间，并请确保完成以下步骤：

| 依赖 | whisperX 🖥️ | whisperX ☁️ |
|:-----|:-------------------|:----------------|
| Anaconda 🐍 | [下载](https://www.anaconda.com/download/success) | [下载](https://www.anaconda.com/download/success) |
| Git 🌿 | [下载](https://git-scm.com/download/win) | [下载](https://git-scm.com/download/win) |
| Cuda Toolkit 12.6 🚀 | [下载](https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe) | - |
| Cudnn 9.3.0 🧠 | [下载](https://developer.download.nvidia.com/compute/cudnn/9.3.0/local_installers/cudnn_9.3.0_windows.exe) | - |

> 注意：安装Anaconda时必须勾选"使用桌面开发的C++"，安装完成后需要重启计算机。🔄

### 安装步骤

支持Win, Mac, Linux。遇到问题可以把整个步骤丢给 GPT 问问~
1. 打开 Anaconda Powershell Prompt 并切换到桌面目录：
   ```bash
   cd desktop
   ```

2. 克隆项目：
   ```bash
   git clone https://github.com/Huanshere/VideoLingo.git
   cd VideoLingo
   ```

3. 配置虚拟环境（必须 3.10.0）：
   ```bash
   conda create -n videolingo python=3.10.0
   conda activate videolingo
   ```

4. 运行安装脚本：
   ```bash
   python install.py
   ```
   根据提示选择所需的 Whisper 项目，脚本将自动安装相应的 torch 和 whisper 版本

   注意：Mac 用户需根据提示手动安装 ffmpeg

5. 🎉 启动 Streamlit 应用：
   ```bash
   streamlit run st.py
   ```

6. 在弹出网页的侧边栏中设置key，并注意选择whisper方法

   ![settings](https://github.com/user-attachments/assets/3d99cf63-ab89-404c-ae61-5a8a3b27d840)