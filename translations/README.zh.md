<div align="center">

<img src="/docs/logo.png" alt="VideoLingo Logo" height="140">

# 连接世界每一帧

<a href="https://trendshift.io/repositories/12200" target="_blank"><img src="https://trendshift.io/api/badge/repositories/12200" alt="Huanshere%2FVideoLingo | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

[**English**](/README.md)｜[**简体中文**](/translations/README.zh.md)｜[**繁體中文**](/translations/README.zh-TW.md)｜[**日本語**](/translations/README.ja.md)｜[**Español**](/translations/README.es.md)｜[**Русский**](/translations/README.ru.md)｜[**Français**](/translations/README.fr.md)

**QQ群：875297969**

</div>

## 🌟 简介（[在线体验！](https://videolingo.io)）

VideoLingo 在 Streamlit 界面中整合语音识别、字幕翻译、分句和配音，可生成字幕文件，以及可选的字幕视频或配音视频。翻译质量取决于原始音频、语言和所选模型。

主要特点和功能：
- 🎥 使用 yt-dlp 从 Youtube 链接下载视频

- 使用 WhisperX 进行词级语音识别与时间对齐

- **📝 使用 NLP 和 AI 进行字幕分割**

- **📚 自定义 + AI 生成术语库，保证翻译连贯性**

- 直译，以及可选的反思和自然改写

- 按可配置的长度限制切分字幕

- **🗣️ 支持 GPT-SoVITS、Azure、OpenAI 等多种配音方案**

- 🚀 一键启动，在 streamlit 中一键出片

- 🌍 多语言支持就绪的 streamlit UI

- 📝 详细记录每步操作日志，支持随时中断和恢复进度

- 🔍 模型搜索选择器，自动从 API 获取完整模型列表，支持搜索筛选

- ⏯️ 任务控制 — 处理过程中可随时暂停、继续或停止

在同一个项目中完成转录、翻译、字幕排版和配音。

## 🎥 演示

<table>
<tr>
<td width="33%">

### 双语字幕
---
https://github.com/user-attachments/assets/a5c3d8d1-2b29-4ba9-b0d0-25896829d951

</td>
<td width="33%">

### Cosy2 声音克隆
---
https://github.com/user-attachments/assets/e065fe4c-3694-477f-b4d6-316917df7c0a

</td>
<td width="33%">

### GPT-SoVITS 配音
---
https://github.com/user-attachments/assets/47d965b2-b4ab-4a0b-9d08-b49a7bf3508c

</td>
</tr>
</table>

### 语言支持

**输入语言支持：**

🇺🇸 英语 🤩  |  🇷🇺 俄语 😊  |  🇫🇷 法语 🤩  |  🇩🇪 德语 🤩  |  🇮🇹 意大利语 🤩  |  🇪🇸 西班牙语 🤩  |  🇯🇵 日语 😐  |  🇨🇳 中文* 😊

> *本地识别中文时，请明确选择中文，以使用带标点增强的 Belle Whisper 模型。

翻译语言取决于所选 LLM，配音语言取决于所选 TTS。

## 安装

遇到问题？在[**这里**](https://share.fastgpt.in/chat/share?shareId=066w11n3r9aq6879r4z0v9rh)与我们的免费在线AI助手交流获取帮助。

先安装 [Git](https://git-scm.com/downloads)、[uv](https://docs.astral.sh/uv/getting-started/installation/) 和 [FFmpeg](https://ffmpeg.org/download.html)。安装后重新打开终端，检查 `git --version`、`uv --version` 和 `ffmpeg -version`。

使用 NVIDIA 加速时，需要安装与显卡兼容的驱动。主机安装器根据 `nvidia-smi` 报告的 CUDA 支持版本选择 PyTorch：>=12.8 使用 `cu128`，否则使用 `cu126`；没有 NVIDIA 时使用 CPU 包。这是在选择 Python 包，不会自动安装系统 CUDA Toolkit。本地 WhisperX 的 GPU 识别还需要进程能够找到 CUDA 12 cuBLAS 和 cuDNN 9 库，详见 [GPU 运行库要求](../docs/pages/docs/start.zh-CN.md#gpu-runtime)。

> **注意:** FFmpeg 是必需的，请通过包管理器安装：
> - Windows：从 [FFmpeg 下载页](https://ffmpeg.org/download.html)列出的 Windows 构建中选择**共享库版**，将其 `bin` 目录加入 PATH。
> - macOS：```brew install ffmpeg```（通过 [Homebrew](https://brew.sh/)）
> - Linux：```sudo apt install ffmpeg```（Debian/Ubuntu）

### 使用 uv 安装

uv 自动下载 Python 3.13 并创建隔离的 `.venv`，下面的命令不需要预装 Python。应用支持 Python 3.10–3.13。固定的 TorchCodec 0.7 请配套 **FFmpeg 7 共享库**，仅有 FFmpeg 8/9 不兼容。见[已验证的 Windows 构建](../docs/pages/docs/start.zh-CN.md#ffmpeg-runtime)。

1. 克隆仓库

```bash
git clone https://github.com/Huanshere/VideoLingo.git
cd VideoLingo
```

2. 创建环境并安装依赖

```bash
uv run --no-project --python 3.13 setup_env.py
```

3. 启动应用

```bash
.venv\Scripts\streamlit run st.py        # Windows
.venv/bin/streamlit run st.py            # macOS / Linux
```

或者在 Windows 上双击 `OneKeyStart.bat`。它优先使用已有的 `~/.venvs/videolingo`，其次使用项目 `.venv`。打开 `http://localhost:8501`，在侧栏填写 API 地址、密钥和模型。

### Docker
在 Linux 上部署 NVIDIA GPU 容器，需要 Docker、兼容的显卡驱动和 [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)。镜像使用相同的 Python 3.13 安装流程和应用依赖，默认 CUDA 12.8.1/cu128。匹配的 CUDA 12.6 方案及数据持久化设置见 [Docker 文档](/docs/pages/docs/docker.zh-CN.md)。

```bash
docker build -t videolingo .
docker run -d -p 8501:8501 --gpus all videolingo
```

## API
本项目支持 OpenAI-Like 格式的 api 和多种配音接口：
- LLM：自行选择兼容 OpenAI Chat Completions、能够返回流程所需结构化 JSON 的服务和模型。推荐 [OpenLux](https://www.openlux.ai/register?aff=wKYu) 中转，API 地址填 `https://api.openlux.ai/v1`。默认性价比高用 GPT-6 Luna，模型 ID 填 `gpt-6-luna`；质量更好用 GPT-6 Sol，模型 ID 填 `gpt-6-sol`；质量最好用 Claude Opus 5.5，模型 ID 填 `claude-opus-5-5`。OpenLux 中转约价见安装文档。在侧栏配置 API 地址、密钥和模型。
- 语音识别：本地运行 WhisperX 或使用 ElevenLabs API。
- TTS：Azure、OpenAI、Fish TTS、SiliconFlow Fish/CosyVoice2、GPT-SoVITS、Edge TTS、F5-TTS，以及 `core/tts_backend/custom_tts.py` 中的自定义适配器。

详细的安装、API 配置、批量说明可以参见文档：[English](/docs/pages/docs/start.en-US.md) | [简体中文](/docs/pages/docs/start.zh-CN.md)

## 当前限制
1. 背景噪音和各语言的对齐模型会影响识别及词级时间戳，人声分离可能有所帮助。数字、符号可能缺少可靠的词级时间，需要检查生成的字幕。

2. LLM 输出需满足流程要求的 JSON 结构，失败时检查 `output/gpt_log/error.json`。重试可能复用已成功的响应缓存和已完成的输出，仅更换模型不会重做所有步骤。不要一开始就删除全部输出。

3. 配音质量和时间匹配取决于翻译、TTS 服务及语速，变速处理不能保证表达自然或完全同步。

4. 本地 WhisperX 每个片段使用一种识别和对齐语言，混合语言语音不保证每种语言的文字和时间都准确。

5. 配音流程不会自动为每个说话人分配不同的声音。

## 📄 许可证

本项目采用 Apache 2.0 许可证，衷心感谢以下开源项目的贡献：

[whisperX](https://github.com/m-bain/whisperX), [yt-dlp](https://github.com/yt-dlp/yt-dlp), [json_repair](https://github.com/mangiucugna/json_repair), [BELLE](https://github.com/LianjiaTech/BELLE)

## 📬 联系

- 加入 QQ 群寻求解答：875297969
- 在 GitHub 上提交 [Issues](https://github.com/Huanshere/VideoLingo/issues) 或 [Pull Requests](https://github.com/Huanshere/VideoLingo/pulls)
- 关注我的 Twitter：[@Huanshere](https://twitter.com/Huanshere)
- 联系邮箱：team@videolingo.io

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo&Timeline)
