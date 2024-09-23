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

- 📝 使用 NLP 和 GPT 根据句意进行字幕分割

- 📚 GPT 总结智能术语知识库，上下文感知翻译

- 🔄 三步直译、反思、意译，告别诡异机翻

- ✅ 按照 Netflix 标准检查单行字幕长度与翻译质量

- 🗣️ 使用 GPT-SoVITS 进行高质量的对齐配音

- 🚀 整合包一键启动，在 streamlit 中一键出片

## 🎥 效果演示

<table>
<tr>
<td width="33%">

### 俄语翻译

https://github.com/user-attachments/assets/25264b5b-6931-4d39-948c-5a1e4ce42fa7

</td>
<td width="33%">

### GPT-SoVITS

https://github.com/user-attachments/assets/47d965b2-b4ab-4a0b-9d08-b49a7bf3508c

</td>
<td width="33%">

### Azure TTS

https://github.com/user-attachments/assets/a5384bd1-0dc8-431a-9aa7-bbe2ea4831b8

</td>
</tr>
</table>

当前支持的所有输入语言和示例：

| 输入语言 | 支持程度 | 翻译demo | 配音demo |
|---------|---------|---------|----------|
| 🇬🇧🇺🇸 英语 | 🤩 | [英转中](https://github.com/user-attachments/assets/127373bb-c152-4b7a-8d9d-e586b2c62b4b) | TODO |
| 🇷🇺 俄语 | 😊 | [俄转中](https://github.com/user-attachments/assets/25264b5b-6931-4d39-948c-5a1e4ce42fa7) | TODO |
| 🇫🇷 法语 | 🤩 | [法转日](https://github.com/user-attachments/assets/3ce068c7-9854-4c72-ae77-f2484c7c6630) | TODO |
| 🇩🇪 德语 | 🤩 | [德转中](https://github.com/user-attachments/assets/07cb9d21-069e-4725-871d-c4d9701287a3) | TODO |
| 🇮🇹 意大利语 | 🤩 | [意转中](https://github.com/user-attachments/assets/f1f893eb-dad3-4460-aaf6-10cac999195e) | TODO |
| 🇪🇸 西班牙语 | 🤩 | [西转中](https://github.com/user-attachments/assets/c1d28f1c-83d2-4f13-a1a1-859bd6cc3553) | TODO |
| 🇯🇵 日语 | 😐 | [日转中](https://github.com/user-attachments/assets/856c3398-2da3-4e25-9c36-27ca2d1f68c2) | TODO |
| 🇨🇳 中文 | 😖 | ❌ | TODO |

翻译语言支持大模型会的所有语言，配音语言取决于选取的TTS方法。

## 🚀 快速开始

### 一键整合包

1. 下载 `v1.1.0` 一键整合包(750M): [CPU版下载](https://vip.123pan.cn/1817874751/8147218) | [度盘备用](https://pan.baidu.com/s/1H_3PthZ3R3NsjS0vrymimg?pwd=ra64)

2. 解压后双击运行文件夹中的 `一键启动.bat`

3. 在弹出的 web 中，在侧边栏配置 api，然后一键出片！

> 💡 提示: 本项目需要配置大模型、WhisperX、TTS，请仔细阅读 [本地安装教程](./docs/install_locally_zh.md)

## 🛠️ 从源码安装

详细的安装指南，包括源码安装和开发环境配置，请参考 [本地安装教程](./docs/install_locally_zh.md)。

本项目采用结构化模块开发，可按顺序逐个运行 `core\step__.py`，技术文档: [中文](./docs/README_guide_zh.md) ｜ [英文](./docs/README_guide_en.md)

## 📄 许可证

本项目采用 MIT 许可证。使用本项目时，请遵循以下规定：

1. 发表作品时请标注字幕由 VideoLingo 生成。
2. 遵循使用的大模型和TTS条约进行备注。

我们衷心感谢以下开源项目的贡献，它们为 VideoLingo 的开发提供了重要支持：

- [whisperX](https://github.com/m-bain/whisperX)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [json_repair](https://github.com/mangiucugna/json_repair)
- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)

## 📬 联系我们

- 加入我们的 QQ 群：875297969
- 在 GitHub 上提交 [Issues](https://github.com/Huanshere/VideoLingo/issues) 或 [Pull Requests](https://github.com/Huanshere/VideoLingo/pulls)

---

<p align="center">如果觉得 VideoLingo 有帮助，请给我们一个 ⭐️！</p>
