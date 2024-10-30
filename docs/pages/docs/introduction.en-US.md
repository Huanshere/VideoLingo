# VideoLingo: Connecting the World, Frame by Frame

## 🌟 Overview

VideoLingo is an all-in-one video translation, localization, and dubbing tool aimed at generating Netflix-quality subtitles. It eliminates stiff machine translations and multi-line subtitles while adding high-quality dubbing, enabling global knowledge sharing across language barriers. With an intuitive Streamlit interface, you can transform a video link into a localized video with high-quality bilingual subtitles and dubbing in just a few clicks.

**Key features:**
- 🎥 YouTube video download via yt-dlp

- 🎙️ Word-level subtitle recognition with WhisperX

- **📝 NLP and GPT-based subtitle segmentation**

- **📚 GPT-generated terminology for coherent translation**

- **🔄 3-step direct translation, reflection, and adaptation for professional-level quality**

- **✅ Netflix-standard single-line subtitles only**

- **🗣️ Dubbing alignment with GPT-SoVITS and other methods**

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
> *Chinese requires separate configuration of the whisperX model, only applicable for local source code installation. See the installation documentation for the configuration process, and be sure to specify the transcription language as zh in the webpage sidebar

Translation language support depends on the capabilities of the large language model used, while dubbing language depends on the chosen TTS method.

## ⚠️ Current Limitations

1. WhisperX performance varies across different devices. Version 1.7 performs demucs voice separation first, but this may result in worse transcription after separation compared to before. This is because whisper itself was trained in environments with background music - before separation it won't transcribe BGM lyrics, but after separation it might transcribe them.

2. **The dubbing feature quality may not be perfect** as it's still in testing and development stage, with plans to integrate MascGCT. For best results currently, it's recommended to choose TTS with similar speech rates based on the original video's speed and content characteristics. See the [demo](https://www.bilibili.com/video/BV1mt1QYyERR/?share_source=copy_web&vd_source=fa92558c28cd668d33dabaddb17e2f9e) for effects.

3. **Multilingual video transcription recognition will only retain the main language**. This is because whisperX uses a specialized model for a single language when forcibly aligning word-level subtitles, and will delete unrecognized languages.

4. **Multi-character separate dubbing is under development**. While whisperX has VAD potential, specific implementation work is needed, and this feature is not yet supported.

## 🚗 Roadmap

- [ ] VAD to distinguish speakers, multi-character dubbing
- [ ] Customizable translation styles
- [ ] SaaS service
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

- Join our Discord: https://discord.gg/9F2G92CWPp
- Submit [Issues](https://github.com/Huanshere/VideoLingo/issues) or [Pull Requests](https://github.com/Huanshere/VideoLingo/pulls) on GitHub
- Follow me on Twitter: [@Huanshere](https://twitter.com/Huanshere)
- Visit the official website: [videolingo.io](https://videolingo.io)
- Email me at: team@.videolingo.io

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo&Timeline)

---

<p align="center">If you find VideoLingo helpful, please give us a ⭐️!</p>
