<div align="center">

<img src="/docs/logo.png" alt="VideoLingo Logo" height="140">

# 连接世界每一帧

[Website](https://videolingo.io) | [Documentation](https://docs.videolingo.io/docs/start)

[**English**](/README.md)｜[**中文**](/i18n/README.zh.md)

**QQ群：875297969**

</div>

## 🌟 项目简介

VideoLingo 是一站式视频翻译本地化配音工具，能够一键生成 Netflix 级别的高质量字幕，告别生硬机翻，告别多行字幕，还能加上高质量的克隆配音，让全世界的知识能够跨越语言的障碍共享。

主要特点和功能：
- 🎥 使用 yt-dlp 从 Youtube 链接下载视频

- **🎙️ 使用 WhisperX 进行单词级时间轴字幕识别**

- **📝 使用 NLP 和 GPT 根据句意进行字幕分割**

- **📚 GPT 总结提取术语知识库，上下文连贯翻译**

- **🔄 三步直译、反思、意译，媲美字幕组精翻效果**

- **✅ 按照 Netflix 标准检查单行长度，绝无双行字幕**

- **🗣️ 使用 FishTTS 等方法对齐克隆配音**

- 🚀 整合包一键启动，在 streamlit 中一键出片

- 📝 详细记录每步操作日志，支持随时中断和恢复进度

与同类项目相比的优势：**绝无多行字幕，最佳的翻译质量，无缝的配音体验**

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

### OAITTS
---
https://github.com/user-attachments/assets/85c64f8c-06cf-4af9-b153-ee9d2897b768

</td>
</tr>
</table>

### 语言支持：

当前输入语言支持和示例：

| 输入语言 | 支持程度 | 翻译demo |
|---------|---------|---------|
| 英语 | 🤩 | [英转中](https://github.com/user-attachments/assets/127373bb-c152-4b7a-8d9d-e586b2c62b4b) |
| 俄语 | 😊 | [俄转中](https://github.com/user-attachments/assets/25264b5b-6931-4d39-948c-5a1e4ce42fa7) |
| 法语 | 🤩 | [法转日](https://github.com/user-attachments/assets/3ce068c7-9854-4c72-ae77-f2484c7c6630) |
| 德语 | 🤩 | [德转中](https://github.com/user-attachments/assets/07cb9d21-069e-4725-871d-c4d9701287a3) |
| 意大利语 | 🤩 | [意转中](https://github.com/user-attachments/assets/f1f893eb-dad3-4460-aaf6-10cac999195e) |
| 西班牙语 | 🤩 | [西转中](https://github.com/user-attachments/assets/c1d28f1c-83d2-4f13-a1a1-859bd6cc3553) |
| 日语 | 😐 | [日转中](https://github.com/user-attachments/assets/856c3398-2da3-4e25-9c36-27ca2d1f68c2) |
| 中文* | 😊 | [中转英](https://github.com/user-attachments/assets/48f746fe-96ff-47fd-bd23-59e9202b495c) |
> *中文需单独配置标点增强后的 whisper 模型，详见安装文档。但效果一般，因为 faster-whisper 加速的 whisper 失去了原有的好的断句，且识别得到的中文没有标点符号，难以断句。同样问题出现在日语上。

翻译语言支持所有语言，配音语言取决于选取的TTS。

## 🚀 快速开始

### 在线体验

商业版（beta）提供免费的 20min 额度，请访问 [videolingo.io](https://videolingo.io)

### Colab 运行 (当前暂不可用)

### 本地安装

VideoLingo 支持所有硬件平台和操作系统，但在 GPU 加速下性能最佳。文档：[English](/docs/pages/docs/start.en-US.md) | [简体中文](/docs/pages/docs/start.zh-CN.md)


### 使用Docker

目前VideoLingo 提供了Dockerfile，可自行使用Dockerfile打包目前VideoLingo，要求CUDA版本为12.4，NVIDIA Driver版本大于550，打包和运行方法为：

```bash
docker build -t videolingo .
docker run -d -p 8501:8501 --gpus all videolingo
```

详见：[Docker](/docs/pages/docs/docker.zh-CN.md)

## 🏭 批量模式（beta）

使用说明: [English](/batch/README.md) | [简体中文](/batch/README.zh.md)

## ⚠️ 当前限制
1. WhisperX 转录效果可能受到视频背景声影响，因为使用了 wav2vac 模型进行对齐，但尽管如此，WhisperX 已经能在 99% 情况下解决 Whisper 本身的幻觉问题。

2. 配音功能由于不同语言的语速和语调差异，还受到前置处理字幕的影响，可能不能 100% 完美，但本项目做了非常多的语速上的工程处理，尽可能保证配音效果。

3. **多语言视频转录识别仅仅只会保留主要语言**，这是由于 whisperX 在强制对齐单词级字幕时使用的是针对单个语言的特化模型，会因为不认识另一种语言而删去。有些商用api可以进行机器自动转换，但实测效果非常一般，因此这个问题目前只能依靠人为切段处理。

4. **多角色分别配音仍在开发**，whisperX 具有 VAD 的潜力（尽管官方承认效果一般），但是具体需要一些施工，暂时没有支持此功能。

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

---

<p align="center">如果觉得 VideoLingo 有帮助，请给我们一个 ⭐️！</p>