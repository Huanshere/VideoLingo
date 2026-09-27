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

- 使用 Qwen3-ASR + Qwen3-ForcedAligner 进行词级语音识别与时间对齐

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

🇺🇸 英语 🤩  |  🇷🇺 俄语 😊  |  🇫🇷 法语 🤩  |  🇩🇪 德语 🤩  |  🇮🇹 意大利语 🤩  |  🇪🇸 西班牙语 🤩  |  🇯🇵 日语 😊  |  🇨🇳 中文 🤩

配音语言取决于所选 TTS。

## 安装

VideoLingo 支持 Windows、macOS（Apple Silicon / Intel）和 Linux。

### 让本地 AI Agent 帮你安装 🤖

如果你的 AI Agent 可以操作这台电脑，直接告诉它：

> `帮我安装 GitHub 上的 Huanshere/VideoLingo，并启动它。`

### Windows 一键安装 🎉

1. 从[最新版本页面](https://github.com/Huanshere/VideoLingo/releases/latest)下载 **Source code (zip)**，解压到桌面等方便找到的位置，并打开文件夹。
2. 双击 `OneKeyStart.bat`，保持窗口打开。首次运行会自动安装 uv、Python 3.12、应用依赖和 FFmpeg，需要联网。
3. 安装完成后，VideoLingo 会自动在浏览器中打开。在侧栏填写 API 地址、密钥和模型，就可以开始使用了。

### 从源码安装（Windows、macOS、Linux）

```bash
git clone https://github.com/Huanshere/VideoLingo.git && cd VideoLingo
uv run start.py
```

以后在 VideoLingo 文件夹中运行 `uv run start.py` 即可启动。Apple Silicon 自动使用 MLX，Intel Mac 使用 CPU 识别。Intel Mac 默认配音只保留新生成的语音，不保留原视频的背景音。

#### Docker（可选）

在 Linux 上部署 NVIDIA GPU 容器，需要 Docker、兼容的显卡驱动和 [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)。镜像使用相同的 Python 3.12 安装流程和应用依赖，默认 CUDA 12.8.1/cu128。匹配的 CUDA 12.6 方案及数据持久化设置见 [Docker 文档](/docs/pages/docs/docker.zh-CN.md)。

```bash
docker build -t videolingo .
docker run -d -p 8501:8501 --gpus all videolingo
```

## HTTP API（替代 Excel 批处理）

Agent 和脚本可以直接使用本地 HTTP API，原来的 Excel 批处理模式已由它替代。
API 与 Streamlit 共用处理流程，保留固定 `output/`，一次执行一个操作。
配置 `config.yaml`，在项目根目录运行下面的命令。首次使用会自动安装缺少的依赖：

```bash
uv run start.py --api
```

输入文件、启动处理、查询进度、下载结果、失败重试和串行批量处理，参见 **[HTTP API 使用文档](../docs/api.md)**。
启动后也可打开 [交互式接口文档](http://localhost:8000/docs)。

## LLM、语音识别与配音服务
本项目支持 OpenAI-Like 格式的 api 和多种配音接口：
- LLM：自行选择兼容 OpenAI Chat Completions、能够返回流程所需结构化 JSON 的服务和模型。推荐 [OpenLux](https://www.openlux.ai/register?aff=wKYu) 中转，API 地址填 `https://api.openlux.ai/v1`。默认性价比高用 GPT-6 Luna，模型 ID 填 `gpt-6-luna`；质量更好用 GPT-6 Sol，模型 ID 填 `gpt-6-sol`；质量最好用 Claude Opus 5.5，模型 ID 填 `claude-opus-5-5`。OpenLux 中转约价见安装文档。在侧栏配置 API 地址、密钥和模型。
- 语音识别：本地运行 Qwen3-ASR + ForcedAligner（默认），或使用 ElevenLabs API。安装器不会安装 WhisperX；若要把它当作后端，见 [WhisperX（手动安装）](../docs/pages/docs/whisperx-manual.zh-CN.md)。
- TTS：Azure、OpenAI、Fish TTS、SiliconFlow Fish/CosyVoice2、GPT-SoVITS、Edge TTS、F5-TTS，以及 `core/tts_backend/custom_tts.py` 中的自定义适配器。

详细的安装、LLM 配置和使用说明可以参见文档：[English](/docs/pages/docs/start.en-US.md) | [简体中文](/docs/pages/docs/start.zh-CN.md)

## 当前限制
1. 背景噪音和各语言的对齐模型会影响识别及词级时间戳，人声分离可能有所帮助。数字、符号可能缺少可靠的词级时间，需要检查生成的字幕。

2. LLM 输出需满足流程要求的 JSON 结构，失败时检查 `output/gpt_log/error.json`。重试可能复用已成功的响应缓存和已完成的输出，仅更换模型不会重做所有步骤。不要一开始就删除全部输出。

3. 配音质量和时间匹配取决于翻译、TTS 服务及语速，变速处理不能保证表达自然或完全同步。

4. 本地识别在每个音频片段中使用一种主要识别和对齐语言，混合语言语音不保证每种语言的文字和时间都准确。

5. 配音流程不会自动为每个说话人分配不同的声音。

## 📄 许可证

本项目采用 Apache 2.0 许可证，衷心感谢以下开源项目的贡献：

[Qwen3-ASR](https://github.com/Qwen/Qwen3-ASR), [MLX Audio](https://github.com/Blaizzy/mlx-audio), [whisperX](https://github.com/m-bain/whisperX), [yt-dlp](https://github.com/yt-dlp/yt-dlp), [json_repair](https://github.com/mangiucugna/json_repair), [BELLE](https://github.com/LianjiaTech/BELLE)

## 📬 联系

- 加入 QQ 群寻求解答：875297969
- 在 GitHub 上提交 [Issues](https://github.com/Huanshere/VideoLingo/issues) 或 [Pull Requests](https://github.com/Huanshere/VideoLingo/pulls)
- 关注我的 Twitter：[@Huanshere](https://twitter.com/Huanshere)
- 联系邮箱：team@videolingo.io

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo&Timeline)
