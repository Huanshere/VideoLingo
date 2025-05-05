# VideoLingo: 连接世界的每一帧

**QQ 群：875297969**

## 🌟 简介（[在线体验！](https://videolingo.io)）

VideoLingo 是一站式视频翻译本地化配音工具，能够一键生成 Netflix 级别的高质量字幕，告别生硬机翻，告别多行字幕，还能加上高质量的克隆配音，让全世界的知识能够跨越语言的障碍共享。

主要特点和功能：
- 🎥 使用 yt-dlp 从 Youtube 链接下载视频

- **🎙️ 使用 WhisperX 进行单词级时间轴字幕识别**

- **📝 使用 NLP 和 GPT 根据句意进行字幕分割**

- **📚 GPT 总结提取术语知识库，上下文连贯翻译**

- **🔄 三步直译、反思、意译，媲美字幕组精翻效果**

- **✅ 按照 Netflix 标准检查单行长度，绝无双行字幕**

- **🗣️ 使用 GPT-SoVITS 等方法对齐克隆配音**

- 🚀 整合包一键启动，在 streamlit 中一键出片

- 📝 详细记录每步操作日志，支持随时中断和恢复进度

与同类项目相比的优势：**绝无多行字幕，最佳的翻译质量，无缝的配音体验**

## 🎥 效果演示

<table>
<tr>
<td width="50%">

### 俄语翻译
---
https://github.com/user-attachments/assets/25264b5b-6931-4d39-948c-5a1e4ce42fa7

</td>
<td width="50%">

### GPT-SoVITS配音
---
https://github.com/user-attachments/assets/47d965b2-b4ab-4a0b-9d08-b49a7bf3508c

</td>
</tr>
</table>

### 语言支持

**输入语言支持：**

🇺🇸 英语 🤩  |  🇷🇺 俄语 😊  |  🇫🇷 法语 🤩  |  🇩🇪 德语 🤩  |  🇮🇹 意大利语 🤩  |  🇪🇸 西班牙语 🤩  |  🇯🇵 日语 😐  |  🇨🇳 中文* 😊

> *中文使用单独的标点增强后的 whisper 模型

**翻译语言支持所有语言，配音语言取决于选取的TTS。**

## 安装

> **注意:** 在 Windows 上使用 NVIDIA GPU 加速需要先完成以下步骤:
> 1. 安装 [CUDA Toolkit 12.6](https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe)
> 2. 安装 [CUDNN 9.3.0](https://developer.download.nvidia.com/compute/cudnn/9.3.0/local_installers/cudnn_9.3.0_windows.exe)
> 3. 将 `C:\Program Files\NVIDIA\CUDNN\v9.3\bin\12.6` 添加到系统环境变量 PATH 中
> 4. 重启电脑

> **注意:** Windows 和 macOS 用户建议通过包管理器（Chocolatey/Homebrew）安装 FFmpeg：
> ```choco install ffmpeg```（Windows）或 ```brew install ffmpeg```（macOS）。
> 如果未安装，程序会在本地下载 FFmpeg。

1. 克隆仓库

```bash
git clone https://github.com/Huanshere/VideoLingo.git
cd VideoLingo
```

2. 安装依赖（需要 `python=3.10`）

```bash
conda create -n videolingo python=3.10.0 -y
conda activate videolingo
python install.py
```

3. 启动应用

```bash
streamlit run st.py
```

### Docker
还可以选择使用 Docker（要求 CUDA 12.4 和 NVIDIA Driver 版本 >550），详见[Docker文档](/docs/pages/docs/docker.zh-CN.md)：

```bash
docker build -t videolingo .
docker run -d -p 8501:8501 --gpus all videolingo
```

## API
本项目支持 OpenAI-Like 格式的 api 和多种配音接口：
- `claude-3-5-sonnet-20240620`, `gpt-4.1`, `deepseek-v3`, ...（按效果排序）
- `azure-tts`, `openai-tts`, `siliconflow-fishtts`, `fish-tts`, `GPT-SoVITS`

详细的安装、 API 配置、汉化、批量说明可以参见文档：[English](/docs/pages/docs/start.en-US.md) | [简体中文](/docs/pages/docs/start.zh-CN.md)

## 当前限制
1. WhisperX 转录效果可能受到视频背景声影响，因为使用了 wav2vac 模型进行对齐。对于背景音乐较大的视频，请开启人声分离增强。另外，如果字幕以数字或特殊符号结尾，可能会导致提前截断，这是因为 wav2vac 无法将数字字符（如"1"）映射到其发音形式（"one"）。

2. 使用较弱模型时容易在中间过程报错，这是因为对响应的 json 格式要求较为严格。如果出现此错误，请删除 `output` 文件夹后更换 llm 重试，否则重复执行会读取上次错误的响应导致同样错误。

3. 配音功能由于不同语言的语速和语调差异，还受到翻译步骤的影响，可能不能 100% 完美，但本项目做了非常多的语速上的工程处理，尽可能保证配音效果。

4. **多语言视频转录识别仅仅只会保留主要语言**，这是由于 whisperX 在强制对齐单词级字幕时使用的是针对单个语言的特化模型，会因为不认识另一种语言而删去。

5. **无法多角色分别配音**，whisperX 的说话人区分效果不够好用。

## 📄 许可证

本项目采用 Apache 2.0 许可证，衷心感谢以下开源项目的贡献：

[whisperX](https://github.com/m-bain/whisperX), [yt-dlp](https://github.com/yt-dlp/yt-dlp), [json_repair](https://github.com/mangiucugna/json_repair), [BELLE](https://github.com/LianjiaTech/BELLE)

## 📬 联系我们

- 加入我们的 QQ 群寻求解答：875297969
- 在 GitHub 上提交 [Issues](https://github.com/Huanshere/VideoLingo/issues) 或 [Pull Requests](https://github.com/Huanshere/VideoLingo/pulls)
- 关注我的 Twitter：[@Huanshere](https://twitter.com/Huanshere)
- 联系邮箱：team@videolingo.io

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo&Timeline)