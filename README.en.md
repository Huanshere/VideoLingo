<div align="center">

# VideoLingo: Connecting the World, Frame by Frame
<p align="center">
  <a href="https://www.python.org" target="_blank"><img src="https://img.shields.io/badge/Python-3.10-blue.svg" alt="Python"></a>
  <a href="https://github.com/Huanshere/VideoLingo/blob/main/LICENSE" target="_blank"><img src="https://img.shields.io/github/license/Huanshere/VideoLingo.svg" alt="License"></a>
  <a href="https://github.com/Huanshere/VideoLingo/stargazers" target="_blank"><img src="https://img.shields.io/github/stars/Huanshere/VideoLingo.svg" alt="GitHub stars"></a>
</p>

[**中文**](README.md) | [**English**](README.en.md)

**QQ Group: 875297969**

</div>

## 🌟 Project Introduction

VideoLingo is an all-in-one video translation and localization tool designed to generate Netflix-quality subtitles, eliminating stiff machine translations and multi-line subtitles, enabling knowledge sharing across language barriers worldwide. Through an intuitive Streamlit web interface, you can complete the entire process from video link to embedded high-quality bilingual subtitles with just a few clicks, easily creating localized videos with Netflix-quality subtitles.

Key features and functionalities:
- Uses yt-dlp to download videos from YouTube links

- Uses WhisperX for word-level timeline subtitle recognition

- Uses NLP and GPT for subtitle segmentation based on sentence meaning

- GPT summarizes intelligent terminology knowledge base for context-aware translation

- Three-step direct translation, reflection, and paraphrasing to eliminate awkward machine translations

- Netflix-standard single-line subtitle length and translation quality checks

- One-click integrated package launch, one-click video production in Streamlit

🚧 VideoLingo is also actively developing voice cloning technology, which will soon support video dubbing, further enhancing the localization experience.

## 🎥 Demo

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

Currently supported input languages and examples:

| Input Language | Support Level | Example Video |
|----------------|---------------|----------------|
| 🇬🇧🇺🇸 English | 🤩 | [English to Chinese demo](https://github.com/user-attachments/assets/127373bb-c152-4b7a-8d9d-e586b2c62b4b) |
| 🇷🇺 Russian | 😊 | [Russian to Chinese demo](https://github.com/user-attachments/assets/25264b5b-6931-4d39-948c-5a1e4ce42fa7) |
| 🇫🇷 French | 🤩 | [French to Japanese demo](https://github.com/user-attachments/assets/3ce068c7-9854-4c72-ae77-f2484c7c6630) |
| 🇩🇪 German | 🤩 | [German to Chinese demo](https://github.com/user-attachments/assets/07cb9d21-069e-4725-871d-c4d9701287a3) |
| 🇮🇹 Italian | 🤩 | [Italian to Chinese demo](https://github.com/user-attachments/assets/f1f893eb-dad3-4460-aaf6-10cac999195e) |
| 🇪🇸 Spanish | 🤩 | [Spanish to Chinese demo](https://github.com/user-attachments/assets/c1d28f1c-83d2-4f13-a1a1-859bd6cc3553) |
| 🇯🇵 Japanese | 😐 | [Japanese to Chinese demo](https://github.com/user-attachments/assets/856c3398-2da3-4e25-9c36-27ca2d1f68c2) |
| 🇨🇳 Chinese | 😖 | ❌ |

Output language supports all languages that Claude can handle.

## 🚀 Quick Start

### One-Click Package Installation

1. Download the `v0.8.0` one-click package (700M): [Direct Link](https://vip.123pan.cn/1817874751/8050534) | [Baidu Backup](https://pan.baidu.com/s/1H_3PthZ3R3NsjS0vrymimg?pwd=ra64)
2. After extracting, double-click `OneKeyStart.bat` in the folder
3. In the opened browser window, make necessary configurations in the sidebar, then create your video with one click!

> 💡 Note: This project requires API keys for large language models and Replicate's API for WhisperX cloud computing 🌩️ <br> For application and configuration of api_keys, please read the [Local Installation Guide](./docs/install_locally_en.md)

### Source Code Installation Method

For detailed installation guide, including source code installation and development environment configuration, please refer to the [Local Installation Guide](./docs/install_locally_en.md).

## 📚 Documentation

- This project uses structured module development, you can run `core\step__.py` in sequence. Technical documentation: [Chinese](./docs/README_guide_zh.md) | [English](./docs/README_guide_en.md)

## 🙏 Acknowledgements

- [whisper-timestamped](https://github.com/linto-ai/whisper-timestamped), [whisperX](https://github.com/m-bain/whisperX), [yt-dlp](https://github.com/yt-dlp/yt-dlp), [json_repair](https://github.com/mangiucugna/json_repair)

## 📄 License

This project is licensed under the MIT License. Please credit VideoLingo for subtitle generation when publishing works.

## 📬 Contact Us

- Join our QQ Group: 875297969
- Submit [Issues](https://github.com/Huanshere/VideoLingo/issues) or [Pull Requests](https://github.com/Huanshere/VideoLingo/pulls) on GitHub

---

<p align="center">If you find VideoLingo helpful, please give us a ⭐️!</p>