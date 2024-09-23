# 🏠 VideoLingo 安装指南

本项目需使用大语言模型、WhisperX 和 TTS ，每个环节都提供了多种选择，**请仔细阅读安装指南😊**

## 📋 API 准备

### 1. **获取大模型的 API_KEY**：

| 模型 | 推荐提供商 | base_url | 价格 | 效果 |
|:-----|:---------|:---------|:-----|:---------|
| claude-3-5-sonnet-20240620 | [云雾 api](https://yunwu.zeabur.app/register?aff=TXMB) | https://yunwu.zeabur.app | ￥15 / 1M | 🤩 |
| Qwen/Qwen2.5-72B-Instruct | [硅基流动](https://cloud.siliconflow.cn/i/ttKDEsxE) | https://api.siliconflow.cn | ￥4 / 1M | 😲 |
> 注：云雾api 还支持 openai 的 tts-1 接口，可在配音步骤使用

#### 常见问题

<details>
<summary>如何选择模型？</summary>

- 🚀 默认使用Qwen2.5, 1h 视频翻译花费约 ￥3。
- 🌟 Claude 3.5 效果更好，翻译的连贯性非常好，且没有 ai 味，但价格更贵。
</details>

<details>
<summary>如何获取 api key？</summary>

1. 点击上面 推荐提供商 的链接
2. 注册账户并充值
3. 在 api key 页面新建一个即可
</details>

<details>
<summary>能用别的模型吗？</summary>

- ✅ 支持 OAI-Like 的 API 接口，需要自行在 streamlit 侧边栏更换。
- ⚠️ 但其余模型遵循指令要求能力弱，非常容易在翻译过程报错，强烈不推荐。
</details>

### 2. **准备 Replicate 的 Token** （仅当使用 replicate 的 whisperX ☁️ 时）

VideoLingo 使用 WhisperX 进行语音识别，支持本地部署和云端api，推荐使用api，下面有api版本的整合包。
#### 方案对比：
| 方案 | 缺点 |
|:-----|:-----|
| **whisperX 🖥️** | • 安装CUDA 🛠️<br>• 下载模型 📥<br>• 高显存 💾 |
| **whisperX ☁️ (推荐)** | • 需梯子 🕵️‍♂️<br>• Visa卡 💳 |

#### 获取令牌
   - 在 [Replicate](https://replicate.com/account/api-tokens) 注册并绑定 Visa 卡支付方式，获取令牌
   - 或加入 QQ 群在群公告中免费获取测试令牌

### 3. **TTS 的 API**
VideoLingo提供了多种tts接入方式，以下是对比（如不使用配音仅翻译请跳过）

| TTS 方案 | 优点 | 缺点 | 中文效果 | 非中文效果 |
|:---------|:-----|:-----|:---------|:-----------|
| 🎙️ OpenAI TTS | 质量高情感真实 | 中文听起来像外国人 | 😕 | 🤩 |
| 🎤 Edge TTS | 免费 | 烂大街 | 😊 | 😊 |
| 🔊 Azure TTS (推荐) | 中文效果自然 | 充值不方便 | 🤩 | 😃 |
| 🗣️ GPT-SoVITS (beta) | 本地，克隆，中文无敌 | 目前只支持英文输入中文输出，需要显卡训练模型，最好用于 无明显bgm 的单人视频，且底模最好与原声相近 | 😱 | 🚫 |

对于OpenAI TTS，推荐使用 [云雾 api](https://yunwu.zeabur.app/register?aff=TXMB)。
Edge TTS 免配置，Azure TTS 可在QQ群获取免费 key或自行注册。后续在 VideoLingo运行网页 的侧边栏进行配置。

<details>
<summary>GPT-SoVITS 的使用教程（仅支持 v2 新版本）</summary>

1. 前往 [官方的语雀文档](https://www.yuque.com/baicaigongchang1145haoyuangong/ib3g1e/dkxgpiy9zb96hob4#KTvnO) 查看配置要求并下载整合包。

2. 将 `GPT-SoVITS-v2-xxx` 放置在与 `VideoLingo` 同级目录下。**注意是并列而不是包含。**

3. 选择以下任一方式配置模型：

   a. 自训练模型：
   - 训练好模型后， `GPT-SoVITS-v2-xxx\GPT_SoVITS\configs` 下的 `tts_infer.yaml` 已自动填写好你的模型地址，将其复制并重命名为 `你喜欢的角色名.yaml`
   - 在和 `yaml` 文件同个目录下，放入后续使用的参考音频，命名为 `你喜欢的角色名_参考音频的文字内容.wav` 或 `.mp3`，例如 `Huanyuv2_你好，这是一条测试音频.wav`
   - 在 VideoLingo 网页的侧边栏中，将 `GPT-SoVITS 角色` 配置为 `你喜欢的角色名`。

   b. 使用预训练模型：
   - 从 [这里](https://vip.123pan.cn/1817874751/8137723) 下载我的模型，解压后覆盖到 `GPT-SoVITS-v2-xxx`。
   - 在 `GPT-SoVITS 角色` 配置为 `Huanyuv2`。

   c. 使用其他训练好的模型：
   - 将模型文件分别放在 `GPT_weights_v2` 和 `SoVITS_weights_v2` 下。
   - 参考方法 a，重命名并修改 `tts_infer.yaml` 中的路径指向你的两个模型。
   - 参考方法 a，在和 `yaml` 文件同个目录下，放入后续使用的参考音频，命名为 `你喜欢的角色名_参考音频的文字内容.wav` 或 `.mp3`

   ```
   # 目录结构示意
   .
   ├── VideoLingo
   │   └── ...
   └── GPT-SoVITS-v2-xxx
       ├── GPT_SoVITS
       │   └── configs
       │       ├── tts_infer.yaml
       │       ├── 你喜欢的角色名.yaml
       │       └── 你喜欢的角色名_参考音频的文字内容.wav
       ├── GPT_weights_v2
       │   └── [你的GPT模型文件]
       └── SoVITS_weights_v2
           └── [你的SoVITS模型文件]
   ```
        
配置完成后，VideoLingo 在配音步骤时会自动在弹出的命令行中打开 GPT-SoVITS 的推理 API 端口。配音完成后可手动关闭。注意，此方法仍然不够稳定，容易出现漏字漏句，请谨慎使用。</details>


## 🚀 一键整合包

### 注意事项：

1. 整合包使用的是 CPU 版本的 torch，大小约 **2.5G**。
2. 在配音步骤使用 UVR5 降噪时，CPU 版本会显著慢于 GPU 加速的 torch。
3. 整合包**仅支持通过 API 调用 whisperX ☁️**，不支持本地运行 whisperX 💻。
4. 由于技术原因，整合包**无法在配音时使用 edge-tts**，除此之外功能完整。

如果需要以下功能，请从源码安装（需要Nvidia显卡以及至少 **20G** 硬盘空间）：
- 本地运行 whisperX 💻
- 使用 GPU 加速的 UVR5 降噪

### 使用说明

1. 下载 `v1.0.0` 一键整合包(750M): [CPU版下载](https://vip.123pan.cn/1817874751/8117948) | [度盘备用](https://pan.baidu.com/s/1H_3PthZ3R3NsjS0vrymimg?pwd=ra64)

2. 解压后双击运行文件夹中的 `一键启动.bat`

3. 在打开的浏览器窗口中，在侧边栏进行必要配置，然后一键出片！
  ![settings](https://github.com/user-attachments/assets/3d99cf63-ab89-404c-ae61-5a8a3b27d840)

## 🛠️ 源码安装流程

### Windows 前置依赖

在开始安装 VideoLingo 之前，注意预留 **20G** 硬盘空间，并请确保完成以下步骤：

| 依赖 | whisperX 🖥️ | whisperX ☁️ |
|:-----|:-------------------|:----------------|
| Miniconda 🐍 | [下载](https://docs.conda.io/en/latest/miniconda.html) | [下载](https://docs.conda.io/en/latest/miniconda.html) |
| Git 🌿 | [下载](https://git-scm.com/download/win) | [下载](https://git-scm.com/download/win) |
| Cuda Toolkit 12.6 🚀 | [下载](https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe) | - |
| Cudnn 9.3.0 🧠 | [下载](https://developer.download.nvidia.com/compute/cudnn/9.3.0/local_installers/cudnn_9.3.0_windows.exe) | - |

> 注意：安装 Miniconda 时勾选 `添加到系统Path`，安装完成后重启计算机 🔄

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

5. 🎉 输入命令或点击 `一键启动.bat` 启动 Streamlit 应用：
   ```bash
   streamlit run st.py
   ```

6. 在弹出网页的侧边栏中设置key，并注意选择whisper方法

   ![settings](https://github.com/user-attachments/assets/3d99cf63-ab89-404c-ae61-5a8a3b27d840)