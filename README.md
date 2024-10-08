<div align="center">

<img src="/docs/logo.png" alt="VideoLingo Logo" height="140">

# VideoLingo: Connecting the World, Frame by Frame
<p align="center">
  <a href="https://www.python.org" target="_blank"><img src="https://img.shields.io/badge/Python-3.10-blue.svg" alt="Python"></a>
  <a href="https://github.com/Huanshere/VideoLingo/blob/main/LICENSE" target="_blank"><img src="https://img.shields.io/github/license/Huanshere/VideoLingo.svg" alt="License"></a>
  <a href="https://github.com/Huanshere/VideoLingo/stargazers" target="_blank"><img src="https://img.shields.io/github/stars/Huanshere/VideoLingo.svg" alt="GitHub stars"></a>
  <a href="https://colab.research.google.com/github/Huanshere/VideoLingo/blob/main/VideoLingo_colab.ipynb" target="_blank"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a>
</p>

[**English**](/README.md)｜[**中文**](/i18n/README.zh.md) | [**日本語**](/i18n/README.ja.md)


</div>

## 🌟 Overview

VideoLingo is an all-in-one video translation, localization, and dubbing tool aimed at generating Netflix-quality subtitles. It eliminates stiff machine translations and multi-line subtitles while adding high-quality dubbing, enabling global knowledge sharing across language barriers. With an intuitive Streamlit interface, you can transform a video link into a localized video with high-quality bilingual subtitles and dubbing in just a few clicks.

**Key features:**
- 🎥 YouTube video download via yt-dlp

- 🎙️ Word-level subtitle recognition with WhisperX

- **📝 NLP and GPT-based subtitle segmentation**

- **📚 GPT-generated terminology for coherent translation**

- **🔄 2-step translation process rivaling professional quality**

- **✅ Netflix-standard single-line subtitles only**

- 🗣️ Dubbing alignment (e.g., GPT-SoVITS)

- 🚀 One-click startup and output in Streamlit

- 📝 Detailed logging with progress resumption

- 🌐 Comprehensive multi-language support


Difference from similar projects: **Single-line subtitles only, superior translation quality**

## 🎥 Demo

<table>
<tr>
<td width="33%">

### Russian Translation
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

### Language Support:

Current input language support and examples:

| Input Language | Support Level | Translation Demo |
|----------------|---------------|-------------------|
| English | 🤩 | [English to Chinese](https://github.com/user-attachments/assets/127373bb-c152-4b7a-8d9d-e586b2c62b4b) |
| Russian | 😊 | [Russian to Chinese](https://github.com/user-attachments/assets/25264b5b-6931-4d39-948c-5a1e4ce42fa7) |
| French | 🤩 | [French to Japanese](https://github.com/user-attachments/assets/3ce068c7-9854-4c72-ae77-f2484c7c6630) |
| German | 🤩 | [German to Chinese](https://github.com/user-attachments/assets/07cb9d21-069e-4725-871d-c4d9701287a3) |
| Italian | 🤩 | [Italian to Chinese](https://github.com/user-attachments/assets/f1f893eb-dad3-4460-aaf6-10cac999195e) |
| Spanish | 🤩 | [Spanish to Chinese](https://github.com/user-attachments/assets/c1d28f1c-83d2-4f13-a1a1-859bd6cc3553) |
| Japanese | 😐 | [Japanese to Chinese](https://github.com/user-attachments/assets/856c3398-2da3-4e25-9c36-27ca2d1f68c2) |
| Chinese* | 🤩 | [Chinese to English](https://github.com/user-attachments/assets/48f746fe-96ff-47fd-bd23-59e9202b495c) |
> *Chinese requires separate configuration of the whisperX model, see source code installation for details, and be sure to specify the transcription language as zh in the webpage sidebar

Translation language support depends on the capabilities of the large language model used, while dubbing language depends on the chosen TTS method.

## 🚀 Quick Start

### Online Experience

Experience VideoLingo quickly in Colab in just 5 minutes:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Huanshere/VideoLingo/blob/main/VideoLingo_colab.ipynb)

### Local Installation

VideoLingo offers two local installation methods: **One-click Simple Package** and **Source Code Installation**. Please refer to the installation documentation: [English](/docs/pages/docs/start.en-US.md) | [简体中文](/docs/pages/docs/start.zh-CN.md)

## 🏭 Batch Mode

Usage instructions: [English](/batch/README.md) | [简体中文](/batch/README.zh.md)

## ⚠️ Current Limitations

1. **UVR5 voice separation is resource-intensive** and processes slowly. It's recommended to use this feature only on devices with more than 16GB of RAM and 8GB of VRAM. Note: For videos with loud BGM, not performing voice separation before whisper may cause word-level subtitle adhesion, resulting in errors in the final alignment step.

2. **The quality of dubbing may not be perfect** due to differences in language structure and morpheme information density between source and target languages. For best results, choose TTS with similar speech rates based on the original video's speed and content characteristics. The best practice is to train the original video's voice using GPT-SoVITS, then use "Mode 3: Use every reference audio" for dubbing. This ensures maximum consistency in voice, speech rate, and tone. See the [demo](https://www.bilibili.com/video/BV1mt1QYyERR/?share_source=copy_web&vd_source=fa92558c28cd668d33dabaddb17e2f9e) for effects.

3. **Multilingual video transcription recognition will only retain the main language**. This is because whisperX uses a specialized model for a single language when forcibly aligning word-level subtitles, deleting unrecognized languages.

4. **Multi-character separate dubbing is currently unavailable**. While whisperX has VAD potential, specific development is needed, and this feature is not yet implemented.

## 🚗 Roadmap

- [ ] VAD to distinguish speakers, multi-character dubbing
- [ ] Customizable translation styles
- [ ] User terminology glossary
- [ ] Provide commercial services
- [ ] Lip sync for dubbed videos


## 📄 License

This project is licensed under the Apache 2.0 License. When using this project, please follow these rules:

1. When publishing works, it is **recommended (not mandatory) to credit VideoLingo for subtitle generation**.
2. Follow the terms of the large language models and TTS used for proper attribution.
3. If you copy the code, please include the full copy of the Apache 2.0 License.

We sincerely thank the following open-source projects for their contributions, which provided important support for the development of VideoLingo:

- [whisperX](https://github.com/m-bain/whisperX)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [json_repair](https://github.com/mangiucugna/json_repair)
- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)
- [BELLE](https://github.com/LianjiaTech/BELLE)

## 📬 Contact Us

- Join our QQ Group: 875297969
- Submit [Issues](https://github.com/Huanshere/VideoLingo/issues) or [Pull Requests](https://github.com/Huanshere/VideoLingo/pulls) on GitHub
- Follow me on Twitter: [@Huanshere](https://twitter.com/Huanshere)
- Visit the official website: [videolingo.io](https://videolingo.io)

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo&Timeline)

---

<p align="center">If you find VideoLingo helpful, please give us a ⭐️!</p>