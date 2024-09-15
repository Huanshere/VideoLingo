<div align="center">

# 🌉 VideoLingo: 连接世界的每一帧

![Python](https://img.shields.io/badge/python-v3.12-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![GitHub stars](https://img.shields.io/github/stars/Huanshere/VideoLingo.svg)

[**中文**](README.md) | [**English**](README.en.md)

[**b站演示**](https://www.bilibili.com/video/BV1QsYXeGEPP/)

**QQ群：875297969**

</div>

## 🌟 初衷

VideoLingo 是一站式视频翻译本地化工具，旨在生成 Netflix 级别的高质量字幕，告别生硬机翻，告别多行字幕，让全世界的知识能够跨越语言的障碍共享。

VideoLingo 能够自动下载视频、提取音频、进行高精度的语音识别、生成字幕、执行高质量的文本翻译和字幕对齐，并将翻译后的字幕无缝集成到原始视频中。通过直观的 Streamlit 网页界面，只需点击几下就能完成整个流程，轻松创建出具有 Netflix 品质字幕的本地化视频。

VideoLingo 还在积极开发声音克隆技术，很快将支持视频配音，进一步提升视频的本地化体验。无论是内容创作者、教育工作者还是多语言传播需求者，VideoLingo 都能成为强大的助手，帮助跨越语言障碍，连接全球观众。

> 看看效果吧！💪

<table>
<tr>
<td width="50%">

https://github.com/user-attachments/assets/127373bb-c152-4b7a-8d9d-e586b2c62b4b

</td>
<td width="50%">

https://github.com/user-attachments/assets/25264b5b-6931-4d39-948c-5a1e4ce42fa7

</td>
</tr>
</table>

## ✨ 特点

- 使用 WhisperX 进行单词级时间轴字幕识别

- 使用 NLP 和 GPT 根据句意进行字幕分割

- GPT 总结智能术语知识库，实现上下文感知翻译

- 三步直译、反思、意译，告别诡异机翻

- Netflix 级别的单行字幕长度与翻译质量

- 一键整合包启动，在 streamlit 中一键出片！

- 开发者友好：逐步结构化文件，便于自定义开发 : [中文技术文档](./docs/README_guide_zh.md) | [英文技术文档](./docs/README_guide_en.md) 
    > 你甚至可以单独运行每一个`core`下的`step__.py`文件！   


## 🏠 [本地安装教程](./docs/install_locally_zh.md)

## 🚧 当前限制

我们正在不断改进VideoLingo，但目前仍存在一些限制：

- 音频长度：目前仅支持30分钟以内的视频，我们计划很快扩展这一限制。

- 输入语言支持：

| 输入语言 | 支持程度 | 示例视频 |
|---------|---------|---------|
| 🇬🇧🇺🇸 英语 | 🤩 | [英转中 demo](https://github.com/user-attachments/assets/127373bb-c152-4b7a-8d9d-e586b2c62b4b)  |
| 🇷🇺 俄语 | 😊 | [俄转中 demo](https://github.com/user-attachments/assets/25264b5b-6931-4d39-948c-5a1e4ce42fa7) |
| 🇫🇷 法语 | 🤩 | [法转日 demo](https://github.com/user-attachments/assets/3ce068c7-9854-4c72-ae77-f2484c7c6630)|
| 🇩🇪 德语 | 🤩 | [德转中 demo](https://github.com/user-attachments/assets/07cb9d21-069e-4725-871d-c4d9701287a3) |
| 🇮🇹 意大利语 | 🤩 | [意转中 demo](https://github.com/user-attachments/assets/f1f893eb-dad3-4460-aaf6-10cac999195e) |
| 🇪🇸 西班牙语 | 🤩 | [西转中 demo](https://github.com/user-attachments/assets/c1d28f1c-83d2-4f13-a1a1-859bd6cc3553) |
| 🇯🇵 日语 | 😐 | [日转中 demo](https://github.com/user-attachments/assets/856c3398-2da3-4e25-9c36-27ca2d1f68c2) |
| 🇨🇳 中文 | 😖 | ❌ |

😖 whisper 识别中文字词级时间轴时难以给出标点符号。

- 输出语言支持：VideoLingo 支持翻译成claude会的所有语言

## 🙏 致谢

感谢以下开源项目的贡献：

- [whisper-timestamped](https://github.com/linto-ai/whisper-timestamped): 为Whisper添加时间戳功能的扩展
- [whisperX](https://github.com/m-bain/whisperX): 为Whisper添加时间戳功能的扩展
- [yt-dlp](https://github.com/yt-dlp/yt-dlp): 用于下载YouTube视频和其他网站内容的命令行工具
- [json_repair](https://github.com/mangiucugna/json_repair): 超无敌的 修复解析 gpt 的 json 输出的库，无缝替代 json.loads

## 🤝 欢迎贡献

我们欢迎所有形式的贡献，如果有任何想法或建议，请随时提出issue或提交pull request。

如需进一步交流或寻求帮助，欢迎加入我们的QQ群

## Star 历史

[![Star 历史图表](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo)
