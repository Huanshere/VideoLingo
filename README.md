# 🌉 VideoLingo: 连接世界的每一帧

![Python](https://img.shields.io/badge/python-v3.12-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
<a href="https://colab.research.google.com/github/Huanshere/VideoLingo/blob/main/Colab_VideoLingo.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="在 Colab 中打开"/></a>
![GitHub stars](https://img.shields.io/github/stars/Huanshere/VideoLingo.svg)

[中文](README.md) | [English](README.en.md)

🎥✨ 厌倦了杂乱的 YouTube 翻译？发现无缝视频本地化的魔力吧！

## 🌟 我们提供什么

- 🎬 Netflix 品质的字幕：告别业余翻译！
  
- 💰 极低成本：仅需 2 元即可创作 5 分钟的跨语言字幕。
  
- 🤖 利用 NLP 和 LLM 进行专业级翻译和字幕对齐。

- 🎤 个性化配音的语音克隆（测试版功能）。

> 看看我们的演示吧！🚀💪

https://github.com/user-attachments/assets/c5e2caa5-99f6-435c-ae3b-bf8fd233bb7b

## 💡 特点

- 📚 NLP 和 LLM 驱动的字幕分割

- 🧠 智能术语知识库，实现上下文感知翻译

- 🔄 三步翻译过程：直接翻译 - 反思 - 改进

- 🎯 精确的单词级字幕对齐

- 🎤 GPT-SoVits 高质量的个性化配音

- 👨‍💻 开发者友好：逐步结构化文件，便于自定义

- 📘 全面的文档：[英文指南](./docs/README_guide_en.md) | [中文指南](./docs/README_guide_zh.md)

## 🎯 如何使用

1. 下载 release 中的一键启动包（推荐）

2. 配置 `config.py` 中的 api_key

3. 点击 `一键启动.bat` 启动 Streamlit

4. 开始使用 VideoLingo！

## 🚀 从头安装

> **注意**：此安装指南适用于 Mac 和 Windows 系统。
> 但此版本只有字幕翻译部分，需要配音功能请下载一键启动包。

1. 克隆仓库：
   ```bash
   git clone https://github.com/Huanshere/VideoLingo.git
   cd VideoLingo
   ```

2. 设置并激活 Conda 虚拟环境：
   ```bash
   conda create -n videolingo python=3.12.0
   conda activate videolingo
   ```

3. 配置`config.py`

4. 执行安装脚本：
   ```bash
   python install.py
   ```

🎉 恭喜！您的 VideoLingo 环境现在已准备就绪。

## 🛣️ 路线图

- [] 优化 tts 语气

## Star 历史

[![Star 历史图表](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo)