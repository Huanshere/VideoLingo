<div align="center">

<img src="/docs/logo.png" alt="VideoLingo Logo" height="140">

# VideoLingo: 连接世界的每一帧
<p align="center">
  <a href="https://www.python.org" target="_blank"><img src="https://img.shields.io/badge/Python-3.10-blue.svg" alt="Python"></a>
  <a href="https://github.com/Huanshere/VideoLingo/blob/main/LICENSE" target="_blank"><img src="https://img.shields.io/github/license/Huanshere/VideoLingo.svg" alt="License"></a>
  <a href="https://github.com/Huanshere/VideoLingo/stargazers" target="_blank"><img src="https://img.shields.io/github/stars/Huanshere/VideoLingo.svg" alt="GitHub stars"></a>
  <a href="https://colab.research.google.com/github/Huanshere/VideoLingo/blob/main/VideoLingo_colab.ipynb" target="_blank"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a>
</p>

[**English**](/README.md)｜[**中文**](/i18n/README.zh.md) | [**日本語**](/i18n/README.ja.md)

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

- **🗣️ 使用 GPT-SoVITS 等方法对齐配音**

- 🚀 整合包一键启动，在 streamlit 中一键出片

- 📝 详细记录每步操作日志，支持随时中断和恢复进度

- 🌐 全面的多语言支持，轻松实现跨语言视频本地化

与同类项目的主要区别：**绝无多行字幕，最佳的翻译质量**

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
| 中文* | 🤩 | [中转英](https://github.com/user-attachments/assets/48f746fe-96ff-47fd-bd23-59e9202b495c) |
> *中文需单独配置whisperX模型，详见源码安装，并注意在网页侧边栏指定转录语言为zh

翻译语言支持大模型会的所有语言，配音语言取决于选取的TTS方法。

## 🚀 快速开始

### 在线体验

只需 5 分钟即可在 Colab 中快速体验 VideoLingo：

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Huanshere/VideoLingo/blob/main/VideoLingo_colab.ipynb)

### 本地安装

VideoLingo 提供 **一键简易包** 和 **源码安装** 两种本地安装方式，请参考安装文档：[English](/docs/pages/docs/start.en-US.md) | [简体中文](/docs/pages/docs/start.zh-CN.md)

## 🏭 批量模式

使用说明: [English](/batch/README.md) | [简体中文](/batch/README.zh.md)

## ⚠️ 当前限制

1. **UVR5 人声分离对系统资源要求较高**，处理速度较慢。建议仅在拥有 16GB 以上内存和 8GB 以上显存的设备上勾选使用此功能。注意：对于BGM过吵的视频，如果不在 whisper 前进行人声分离，很可能会导致单词级字幕黏连，在最后的对齐步骤抛出错误。

   
2. **配音功能的质量可能不完美**，归根结底是因为语言结构差异、以及源语言与目标语言之间的语素信息密度不同。为获得最佳效果，建议根据原视频的语速和内容特点，选择相近语速的 TTS。最佳实践是使用GPT-SoVITS训练原视频声音，然后采取 `模式3:使用每一条参考音频` 进行配音，这样能最大程度保证音色、语速、语气的吻合，效果见 [demo](https://www.bilibili.com/video/BV1mt1QYyERR/?share_source=copy_web&vd_source=fa92558c28cd668d33dabaddb17e2f9e)。

3. **多语言视频转录识别仅仅只会保留主要语言**，这是由于 whisperX 在强制对齐单词级字幕时使用的是针对单个语言的特化模型，会因为不认识另一种语言而删去。

4. **多角色分别配音暂不可用**，whisperX 具有 VAD 的潜力，但是具体需要一些施工，暂时没有开发此功能。

## 🚗 路线图

- [ ] VAD 区分说话人，多角色配音
- [ ] 翻译风格自定义
- [ ] 用户术语表
- [ ] 提供商业化服务
- [ ] 配音视频唇形同步

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
- [BELLE](https://github.com/LianjiaTech/BELLE)

## 📬 联系我们

- 加入我们的 QQ 群：875297969
- 在 GitHub 上提交 [Issues](https://github.com/Huanshere/VideoLingo/issues) 或 [Pull Requests](https://github.com/Huanshere/VideoLingo/pulls)
- 关注我的 Twitter：[@Huanshere](https://twitter.com/Huanshere)
- 访问官方网站：[videolingo.io](https://videolingo.io)

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo&Timeline)

---

<p align="center">如果觉得 VideoLingo 有帮助，请给我们一个 ⭐️！</p>