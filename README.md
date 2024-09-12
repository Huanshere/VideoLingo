<div align="center">

# 🌉 VideoLingo: 连接世界的每一帧

![Python](https://img.shields.io/badge/python-v3.12-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![GitHub stars](https://img.shields.io/github/stars/Huanshere/VideoLingo.svg)

[**中文**](README.md) | [**English**](README.en.md)

[**b站演示**](https://www.bilibili.com/video/BV1QsYXeGEPP/)

**QQ群：875297969**

</div>

## 🌟 能做什么

- 🍖 全自动视频搬运工，生成 Netflix 品质的字幕！

- 🎤 克隆自己的声音进行配音!（🚧 仍在开发中）

- ✨ 在 streamlit 中点击-完成！

![demo.png](https://files.catbox.moe/clsmt9.png)

> 看看效果吧！💪

<table>
<tr>
<td width="60%">

https://github.com/user-attachments/assets/0f5d5878-bfa5-41e4-ade1-d2b81d925a7d

</td>
</tr>
</table>

## ✨ 特点

- 使用 NLP 和 LLM 进行字幕分割

- 智能术语知识库，实现上下文感知翻译

- 三步翻译过程：直接翻译 - 反思 - 改进

- 精确的单词级字幕对齐

- 仅需 1 元即可创作 5 分钟的 Netflix 级双语字幕

- 开发者友好：逐步结构化文件，便于自定义开发 : [中文技术文档](./docs/README_guide_zh.md) | [英文技术文档](./docs/README_guide_en.md) 
    > 你甚至可以单独运行每一个`core`下的`step__.py`文件！   


## 🏠 本地部署（Windows）

本项目需要安装多个依赖项，对用户的动手能力有一定要求。安装指南请 [点击此处](./docs/install_locally_zh.md) 查看


### Docker一键部署

拉取镜像：

```bash
docker pull sguann/videolingo_app:latest
```

运行镜像：
```bash
docker run -d -p 8501:8501 -e API_KEY=xxx -e BASE_URL=xxx -e WHISPER_METHOD=xxx -e DISPLAY_LANGUAGE=xxx sguann/videolingo_app:latest
```

其中:

 - `API_KEY` 访问token,需要自行申请
 - `BASE_URL` 模型地址，默认"https://api.deepseek.com"
 - `WHISPER_METHOD` Whisper模型，可选项分别为：`whisper_timestamped`、`whisperX`、`whisperX_api`, 默认`whisper_timestamped`
 - `DISPLAY_LANGUAGE` 显示语言，可选`zh_CN`, `zh_TW`, `en_US`, `ja_JP`, 默认`auto`

## ⚡️ 快速体验

我们已将项目部署至[趋动云-VideoLingo平台](https://open.virtaicloud.com/web/project/detail/480194078119297024)（请注意：当前仅更新至v0.2版本），可以轻松克隆并启动项目体验，详细的图文教程请 [点击此处](docs/趋动云使用说明.md) 查看。

## 🚧 当前限制和未来改进

我们正在不断改进VideoLingo，但目前仍存在一些限制：

| 限制 | 当前 | 计划 |
|------|----------|--------------|
| 音频长度 | 仅支持30分钟以内 | 将很快扩展这一限制 |
| 多语言支持 | 英语识别效果较好<br>日语识别效果一般<br>中文识别非常不稳定且容易报错 | 引入针对不同语言的专门模型 |

## 🙏 致谢

感谢以下开源项目的贡献:

- [whisper](https://github.com/openai/whisper): OpenAI的开源自动语音识别系统
- [whisper-timestamped](https://github.com/linto-ai/whisper-timestamped): 为Whisper添加时间戳功能的扩展
- [whisperX](https://github.com/m-bain/whisperX): 为Whisper添加时间戳功能的扩展
- [yt-dlp](https://github.com/yt-dlp/yt-dlp): 用于下载YouTube视频和其他网站内容的命令行工具
- [GPT-SoVITS](https://github.com/RVC-Project/GPT-SoVITS) & [GPT-SoVITS-Inference](https://github.com/X-T-E-R/GPT-SoVITS-Inference): 基于GPT和SoVITS的语音合成系统及推理库
- [FFmpeg](https://github.com/FFmpeg/FFmpeg): 用于处理多媒体内容的完整多平台解决方案
- [Ultimate Vocal Remover GUI v5 (UVR5)](https://github.com/Anjok07/ultimatevocalremovergui): 用于分离音乐中的人声和伴奏的工具
- [json_repair](https://github.com/mangiucugna/json_repair): 超无敌的 修复解析 gpt 的 json 输出的库，无缝替代 json.loads

## 🤝 欢迎贡献

我们欢迎所有形式的贡献，如果有任何想法或建议，请随时提出issue或提交pull request。

如需进一步交流或寻求帮助，欢迎加入我们的QQ群

## Star 历史

[![Star 历史图表](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo)
