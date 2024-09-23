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

VideoLingo is an all-in-one video translation and localization dubbing tool, aimed at generating Netflix-quality subtitles, eliminating stiff machine translations and multi-line subtitles, while also adding high-quality dubbing. It enables knowledge sharing across language barriers worldwide. Through an intuitive Streamlit web interface, you can complete the entire process from video link to embedded high-quality bilingual subtitles and even dubbing with just a few clicks, easily creating Netflix-quality localized videos.

Key features and functionalities:
- 🎥 Uses yt-dlp to download videos from YouTube links

- 🎙️ Uses WhisperX for word-level timeline subtitle recognition

- 📝 Uses NLP and GPT for subtitle segmentation based on sentence meaning

- 📚 GPT summarizes intelligent terminology knowledge base for context-aware translation

- 🔄 Three-step direct translation, reflection, and paraphrasing to eliminate awkward machine translations

- ✅ Netflix-standard single-line subtitle length and translation quality checks

- 🗣️ Uses GPT-SoVITS for high-quality aligned dubbing

- 🚀 One-click integrated package launch, one-click video production in Streamlit

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

| Input Language | Support Level | Translation Demo | Dubbing Demo |
|----------------|---------------|-------------------|--------------|
| 🇬🇧🇺🇸 English | 🤩 | [English to Chinese](https://github.com/user-attachments/assets/127373bb-c152-4b7a-8d9d-e586b2c62b4b) | TODO |
| 🇷🇺 Russian | 😊 | [Russian to Chinese](https://github.com/user-attachments/assets/25264b5b-6931-4d39-948c-5a1e4ce42fa7) | TODO |
| 🇫🇷 French | 🤩 | [French to Japanese](https://github.com/user-attachments/assets/3ce068c7-9854-4c72-ae77-f2484c7c6630) | TODO |
| 🇩🇪 German | 🤩 | [German to Chinese](https://github.com/user-attachments/assets/07cb9d21-069e-4725-871d-c4d9701287a3) | TODO |
| 🇮🇹 Italian | 🤩 | [Italian to Chinese](https://github.com/user-attachments/assets/f1f893eb-dad3-4460-aaf6-10cac999195e) | TODO |
| 🇪🇸 Spanish | 🤩 | [Spanish to Chinese](https://github.com/user-attachments/assets/c1d28f1c-83d2-4f13-a1a1-859bd6cc3553) | TODO |
| 🇯🇵 Japanese | 😐 | [Japanese to Chinese](https://github.com/user-attachments/assets/856c3398-2da3-4e25-9c36-27ca2d1f68c2) | TODO |
| 🇨🇳 Chinese | 😖 | ❌ | TODO |

Translation languages support all languages that the large language model can handle, while dubbing languages depend on the chosen TTS method.

## 🚀 Quick Start

### One-Click Package Installation

1. Download the `v1.1.0` one-click package (750M): [CPU Version Download](https://vip.123pan.cn/1817874751/8147218) | [Baidu Backup](https://pan.baidu.com/s/1H_3PthZ3R3NsjS0vrymimg?pwd=ra64)

2. After extracting, double-click `OneKeyStart.bat` in the folder

3. In the opened web interface, configure the API in the sidebar, then create your video with one click!

> 💡 Note: This project requires configuration of large language models, WhisperX, and TTS. Please carefully read the [Local Installation Guide](./docs/install_locally_zh.md)

## 🛠️ Source Code Installation

For a detailed installation guide, including source code installation and development environment configuration, please refer to the [Local Installation Guide](./docs/install_locally_zh.md).

This project uses structured module development. You can run `core\step__.py` files in sequence. Technical documentation: [Chinese](./docs/README_guide_zh.md) | [English](./docs/README_guide_en.md)

## 📄 License

This project is licensed under the MIT License. When using this project, please follow these rules:

1. Credit VideoLingo for subtitle generation when publishing works.
2. Follow the terms of the large language models and TTS used for proper attribution.

We sincerely thank the following open-source projects for their contributions, which provided important support for the development of VideoLingo:

- [whisperX](https://github.com/m-bain/whisperX)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [json_repair](https://github.com/mangiucugna/json_repair)
- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)

## 📬 Contact Us

- Join our QQ Group: 875297969
- Submit [Issues](https://github.com/Huanshere/VideoLingo/issues) or [Pull Requests](https://github.com/Huanshere/VideoLingo/pulls) on GitHub

---

<p align="center">If you find VideoLingo helpful, please give us a ⭐️!</p>