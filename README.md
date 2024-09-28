<div align="center">

# VideoLingo: 连接世界的每一帧
<p align="center">
  <a href="https://www.python.org" target="_blank"><img src="https://img.shields.io/badge/Python-3.10-blue.svg" alt="Python"></a>
  <a href="https://github.com/Huanshere/VideoLingo/blob/main/LICENSE" target="_blank"><img src="https://img.shields.io/github/license/Huanshere/VideoLingo.svg" alt="License"></a>
  <a href="https://github.com/Huanshere/VideoLingo/stargazers" target="_blank"><img src="https://img.shields.io/github/stars/Huanshere/VideoLingo.svg" alt="GitHub stars"></a>
</p>

[**中文**](README.md) | [**English**](README.en.md)

**QQ群：875297969**

</div>

## 🌟 项目简介

VideoLingo 是一站式视频翻译本地化配音工具，旨在生成 Netflix 级别的高质量字幕，告别生硬机翻，告别多行字幕，还能加上高质量的配音，让全世界的知识能够跨越语言的障碍共享。通过直观的 Streamlit 网页界面，只需点击两下就能完成从视频链接到内嵌高质量双语字幕甚至带上配音的整个流程，轻松创建 Netflix 品质的本地化视频。

主要特点和功能：
- 🎥 使用 yt-dlp 从 Youtube 链接下载视频

- 🎙️ 使用 WhisperX 进行单词级时间轴字幕识别

- **📝 使用 NLP 和 GPT 根据句意进行字幕分割**

- **📚 GPT 总结提取术语知识库，上下文连贯翻译**

- **🔄 三步直译、反思、意译，媲美字幕组精翻效果**

- **✅ 按照 Netflix 标准检查单行长度，绝无双行字幕**

- 🗣️ 使用 GPT-SoVITS 等方法进行高质量的对齐配音

- 🚀 整合包一键启动，在 streamlit 中一键出片

## 🎥 效果演示

<table>
<tr>
<td width="33%">

### 俄语翻译
---
https://github.com/user-attachments/assets/25264b5b-6931-4d39-948c-5a1e4ce42fa7

</td>
<td width="33%">

### GPT-SoVITS
---
https://github.com/user-attachments/assets/47d965b2-b4ab-4a0b-9d08-b49a7bf3508c

</td>
<td width="33%">

### Fish TTS 丁真
---
https://github.com/user-attachments/assets/e7bb9090-d2ef-4261-9dc5-56bd67dc710d

</td>
</tr>
</table>

### 语言支持：

当前输入语言支持和示例（暂不支持中文输入）：

| 输入语言 | 支持程度 | 翻译demo | 配音demo |
|---------|---------|---------|----------|
| 🇬🇧🇺🇸 英语 | 🤩 | [英转中](https://github.com/user-attachments/assets/127373bb-c152-4b7a-8d9d-e586b2c62b4b) | TODO |
| 🇷🇺 俄语 | 😊 | [俄转中](https://github.com/user-attachments/assets/25264b5b-6931-4d39-948c-5a1e4ce42fa7) | TODO |
| 🇫🇷 法语 | 🤩 | [法转日](https://github.com/user-attachments/assets/3ce068c7-9854-4c72-ae77-f2484c7c6630) | TODO |
| 🇩🇪 德语 | 🤩 | [德转中](https://github.com/user-attachments/assets/07cb9d21-069e-4725-871d-c4d9701287a3) | TODO |
| 🇮🇹 意大利语 | 🤩 | [意转中](https://github.com/user-attachments/assets/f1f893eb-dad3-4460-aaf6-10cac999195e) | TODO |
| 🇪🇸 西班牙语 | 🤩 | [西转中](https://github.com/user-attachments/assets/c1d28f1c-83d2-4f13-a1a1-859bd6cc3553) | TODO |
| 🇯🇵 日语 | 😐 | [日转中](https://github.com/user-attachments/assets/856c3398-2da3-4e25-9c36-27ca2d1f68c2) | TODO |
| 🇨🇳 中文 | 🤩 | TODO | TODO |

翻译语言支持大模型会的所有语言，配音语言取决于选取的TTS方法。

## 🚀 一键整合包 for Windows

### 注意事项：

1. 整合包使用的是 CPU 版本的 torch，大小约 **2.5G**。
2. 在配音步骤使用 UVR5 降噪时，CPU 版本会显著慢于 GPU 加速的 torch。
3. 整合包**仅支持通过 API 调用 whisperXapi ☁️**，不支持本地运行 whisperX 💻。
4. 整合包使用的 whisperXapi 不支持中文转录，若需要使用中文，请从源码安装使用本地运行的 whisperX 💻。

如果需要以下功能，请从源码安装（需要Nvidia显卡以及至少 **20G** 硬盘空间）：
- 输入语言为中文
- 本地运行 whisperX 💻
- 使用 GPU 加速的 UVR5 人声分离

### 下载和使用说明

1. 下载 `v1.2.0` 一键整合包(750M): [直接下载](https://vip.123pan.cn/1817874751/8158115) | [度盘备用](https://pan.baidu.com/s/1H_3PthZ3R3NsjS0vrymimg?pwd=ra64)

2. 解压后双击运行文件夹中的 `一键启动.bat`

3. 在打开的浏览器窗口中，在侧边栏进行必要配置，然后一键出片！
  ![settings](https://github.com/user-attachments/assets/3d99cf63-ab89-404c-ae61-5a8a3b27d840)

> 💡 提示: 本项目需要配置大模型、WhisperX、TTS，请仔细往下阅读 **API 准备**

## 📋 API 准备
本项目需使用大语言模型、WhisperX 和 TTS ，每个环节都提供了多种选择，**请仔细阅读配置指南😊**
### 1. **获取大模型的 API_KEY**：

| 推荐模型 | 推荐提供商 | base_url | 价格 | 效果 |
|:-----|:---------|:---------|:-----|:---------|
| claude-3-5-sonnet-20240620 （默认） | [云雾 api](https://yunwu.zeabur.app/register?aff=TXMB) | https://yunwu.zeabur.app | ￥15 / 1M tokens | 🤩 |
| deepseek-coder | [deepseek](https://platform.deepseek.com/api_keys) | https://api.deepseek.com | ￥2 / 1M tokens | 😲 |
> 注：云雾api 还支持 openai 的 tts-1 接口，可在配音步骤选用。

> 提醒：deepseek在翻译过程有极低的概率错误，若出错请更换sonnet...

#### 常见问题

<details>
<summary>选择哪一个模型好？</summary>

- 🌟 默认使用 Claude 3.5 ，翻译质量极佳，翻译的连贯性非常好，没有 ai 味。
- 🚀 若使用deepseek, 1h 视频翻译花费约 ￥1，效果一般。
</details>

<details>
<summary>如何获取 api key？</summary>

1. 点击上面 推荐提供商 的链接
2. 注册账户并充值
3. 在 api key 页面新建一个即可
4. 云雾api要注意勾选 `无限额度` ，模型处选择 `claude-3-5-sonnet-20240620` 模型，渠道建议选 `纯AZ 1.5倍`
</details>

<details>
<summary>能用别的模型吗？</summary>

- ✅ 支持 OAI-Like 的 API 接口，需要自行在 streamlit 侧边栏更换。
- ⚠️ 但其他模型（尤其是小模型）遵循指令要求能力弱，非常容易在翻译过程报错，强烈不推荐。
</details>

### 2. **准备 Replicate 的 Token** （仅当选用 whisperXapi ☁️ 时）

VideoLingo 使用 WhisperX 进行语音识别，支持本地部署和云端api。
#### 方案对比：
| 方案 | 缺点 |
|:-----|:-----|
| **whisperX 🖥️** | • 安装CUDA 🛠️<br>• 下载模型 📥<br>• 高显存 💾 |
| **whisperXapi ☁️ (推荐)** | • 需梯子 🕵️‍♂️<br>• Visa卡 💳 |

#### 获取令牌
   - 在 [Replicate](https://replicate.com/account/api-tokens) 注册并绑定 Visa 卡支付方式，获取令牌
   - **或加入 QQ 群在群公告中免费获取测试令牌**

### 3. **TTS 的 API**
VideoLingo提供了多种tts接入方式，以下是对比（如不使用配音仅翻译请跳过）

| TTS 方案 | 优点 | 缺点 | 中文效果 | 非中文效果 |
|:---------|:-----|:-----|:---------|:-----------|
| 🎙️ OpenAI TTS | 情感真实 | 中文听起来像外国人 | 😕 | 🤩 |
| 🔊 Azure TTS  | 效果自然 | 充值不方便 | 🤩 | 😃 |
| 🎤 Fish TTS (推荐) | 绝 | 需充值 | 😱 | 😱 |
| 🗣️ GPT-SoVITS (测试) | 本地运行语音克隆 | 目前只支持英文输入中文输出，需要N卡推理模型，最好用于 无明显bgm 的单人视频，且底模最好与原声相近 | 😂 | 🚫 |

- OpenAI TTS，推荐使用 [云雾 api](https://yunwu.zeabur.app/register?aff=TXMB)；
- **Azure TTS 可在QQ群公告获取测试 key** 或自行在 [官网](https://learn.microsoft.com/zh-cn/azure/ai-services/speech-service/get-started-text-to-speech?tabs=windows%2Cterminal&pivots=programming-language-python) 注册充值；
- **Fish TTS 可在QQ群公告获取测试 key** 或自行在 [官网](https://fish.audio/zh-CN/go-api/) 注册充值

<details>
<summary>Azure 声音怎么选？</summary>

建议在 [在线体验](https://speech.microsoft.com/portal/voicegallery) 中试听选择你想要的声音，在右边的代码中可以找到该声音对应的代号，例如 `zh-CN-XiaoxiaoMultilingualNeural`

</details>

<details>
<summary>Fish TTS 声音怎么选？</summary>

前往 [官网](https://fish.audio/zh-CN/) 中试听选择你想要的声音，在 URL 中可以找到该声音对应的代号，例如丁真是 `54a5170264694bfc8e9ad98df7bd89c3`，热门的几种声音已添加在 `config.py` 中，直接修改 `FISH_TTS_CHARACTER` 即可。如需使用其他声音，请在 `config.py` 中修改 `FISH_TTS_CHARACTER_ID_DICT` 字典。

</details>

<details>
<summary>GPT-SoVITS-v2 使用教程</summary>

1. 前往 [官方的语雀文档](https://www.yuque.com/baicaigongchang1145haoyuangong/ib3g1e/dkxgpiy9zb96hob4#KTvnO) 查看配置要求并下载整合包。

2. 将 `GPT-SoVITS-v2-xxx` 与 `VideoLingo` 放在同一个目录下。**注意是两文件夹并列。**

3. 选择以下任一方式配置模型：

   a. 自训练模型：
   - 训练好模型后， `GPT-SoVITS-v2-xxx\GPT_SoVITS\configs` 下的 `tts_infer.yaml` 已自动填写好你的模型地址，将其复制并重命名为 `你喜欢的英文角色名.yaml`
   - 在和 `yaml` 文件同个目录下，放入后续使用的参考音频，命名为 `你喜欢的英文角色名_参考音频的文字内容.wav` 或 `.mp3`，例如 `Huanyuv2_你好，这是一条测试音频.wav`
   - 在 VideoLingo 网页的侧边栏中，将 `GPT-SoVITS 角色` 配置为 `你喜欢的英文角色名`。

   b. 使用预训练模型：
   - 从 [这里](https://vip.123pan.cn/1817874751/8137723) 下载我的模型，解压后覆盖到 `GPT-SoVITS-v2-xxx`。
   - 在 `GPT-SoVITS 角色` 配置为 `Huanyuv2`。

   c. 使用其他训练好的模型：
   - 将 `xxx.ckpt` 模型文件放在 `GPT_weights_v2` 文件夹下，将 `xxx.pth` 模型文件放在 `SoVITS_weights_v2` 文件夹下。
   - 参考方法 a，重命名 `tts_infer.yaml` 文件，并修改文件中的 `custom` 部分的 `t2s_weights_path` 和 `vits_weights_path` 指向你的模型，例如：
  
      ```yaml
      # 示例 方法 b 的配置：
      t2s_weights_path: GPT_weights_v2/Huanyu_v2-e10.ckpt
      version: v2
      vits_weights_path: SoVITS_weights_v2/Huanyu_v2_e10_s150.pth
      ```
   - 参考方法 a，在和 `yaml` 文件同个目录下，放入后续使用的参考音频，命名为 `你喜欢的英文角色名_参考音频的文字内容.wav` 或 `.mp3`，例如 `Huanyuv2_你好，这是一条测试音频.wav`，程序会自动识别并使用。
   - ⚠️ 警告：**请使用英文命名 `角色名`** ，否则会出现错误。 `参考音频的文字内容` 可以使用中文。目前仍处于测试版，可能产生报错。


   ```
   # 期望的目录结构：
   .
   ├── VideoLingo
   │   └── ...
   └── GPT-SoVITS-v2-xxx
       ├── GPT_SoVITS
       │   └── configs
       │       ├── tts_infer.yaml
       │       ├── 你喜欢的英文角色名.yaml
       │       └── 你喜欢的英文角色名_参考音频的文字内容.wav
       ├── GPT_weights_v2
       │   └── [你的GPT模型文件]
       └── SoVITS_weights_v2
           └── [你的SoVITS模型文件]
   ```
        
配置完成后，注意在网页侧边栏选择 `参考音频模式`，VideoLingo 在配音步骤时会自动在弹出的命令行中打开 GPT-SoVITS 的推理 API 端口，配音完成后可手动关闭。注意，此方法仍然不够稳定，容易出现漏字漏句或其他bug，请谨慎使用。</details>

## 🛠️ 源码安装流程

### Windows 前置依赖

在开始安装 VideoLingo 之前，注意预留 **20G** 硬盘空间，并请确保完成以下步骤：

| 依赖 | whisperX 🖥️ | whisperX ☁️ |
|:-----|:-------------------|:----------------|
| Anaconda 🐍 | [下载](https://www.anaconda.com/products/distribution#download-section) | [下载](https://www.anaconda.com/products/distribution#download-section) |
| Git 🌿 | [下载](https://git-scm.com/download/win) | [下载](https://git-scm.com/download/win) |
| Cuda Toolkit 12.6 🚀 | [下载](https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe) | - |
| Cudnn 9.3.0 🧠 | [下载](https://developer.download.nvidia.com/compute/cudnn/9.3.0/local_installers/cudnn_9.3.0_windows.exe) | - |

> 注意：安装 Anaconda 时勾选 `添加到系统Path`，安装完 Cuda 和 Cudnn 后需要重启计算机 🔄

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

3. 配置虚拟环境（**必须 3.10.0**）：
   ```bash
   conda create -n videolingo python=3.10.0 -y
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

<!-- 本项目采用结构化模块开发，可按顺序逐个运行 `core\step__.py`，技术文档: [中文](./docs/README_guide_zh.md) ｜ [英文](./docs/README_guide_en.md)（待更新） -->

## 📄 许可证

本项目采用 Apache 2.0 许可证。使用本项目时，请遵循以下规定：

1. 发表作品时**建议（不强制要求）标注字幕由 VideoLingo 生成**。
2. 遵循使用的大模型和TTS条约进行备注。
3. 如拷贝代码请包含完整的 Apache 2.0 许可证副本。

我们衷心感谢以下开源项目的贡献，它们为 VideoLingo 的开发提供了重要支持：

- [whisperX](https://github.com/m-bain/whisperX)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [json_repair](https://github.com/mangiucugna/json_repair)
- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)

## 📬 联系我们

- 加入我们的 QQ 群：875297969
- 在 GitHub 上提交 [Issues](https://github.com/Huanshere/VideoLingo/issues) 或 [Pull Requests](https://github.com/Huanshere/VideoLingo/pulls)


## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo&Timeline)

---

<p align="center">如果觉得 VideoLingo 有帮助，请给我们一个 ⭐️！</p>
