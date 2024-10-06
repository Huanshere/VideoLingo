# VideoLingo: Connecting the World, Frame by Frame

**QQ Group: 875297969**

## 🌟 Project Introduction

VideoLingo is an all-in-one video translation and localization dubbing tool, aimed at generating Netflix-quality subtitles, eliminating stiff machine translations and multi-line subtitles, while also adding high-quality dubbing. It enables knowledge sharing across language barriers worldwide. Through an intuitive Streamlit web interface, you can complete the entire process from video link to embedded high-quality bilingual subtitles and even dubbing with just a few clicks, easily creating Netflix-quality localized videos.

Key features and functionalities:
- 🎥 Uses yt-dlp to download videos from YouTube links

- 🎙️ Uses WhisperX for word-level timeline subtitle recognition

- **📝 Uses NLP and GPT for subtitle segmentation based on sentence meaning**

- **📚 GPT summarizes and extracts terminology knowledge base for context-aware translation**

- **🔄 Three-step direct translation, reflection, and paraphrasing, rivaling professional subtitle translation quality**

- **✅ Checks single-line length according to Netflix standards, absolutely no double-line subtitles**

- **🗣️ Uses methods like GPT-SoVITS for high-quality aligned dubbing**

- 🚀 One-click integrated package launch, one-click video production in Streamlit

- 📝 Detailed logging of each operation step, supporting interruption and progress resumption at any time

- 🌐 Comprehensive multi-language support, easily achieving cross-language video localization

## 🎥 Demo

<table>
<tr>
<td width="25%">

### Russian Translation
---
https://github.com/user-attachments/assets/25264b5b-6931-4d39-948c-5a1e4ce42fa7

</td>
<td width="25%">

### GPT-SoVITS
---
https://github.com/user-attachments/assets/47d965b2-b4ab-4a0b-9d08-b49a7bf3508c

</td>
<td width="25%">

### Fish TTS Ding Zhen
---
https://github.com/user-attachments/assets/e7bb9090-d2ef-4261-9dc5-56bd67dc710d

</td>
<td width="25%">

### OAITTS
---
https://github.com/user-attachments/assets/85c64f8c-06cf-4af9-b153-ee9d2897b768

</td>
</tr>
</table>

### Language Support:

Currently supported input languages and examples:

| Input Language | Support Level | Translation Demo | Dubbing Demo |
|----------------|---------------|-------------------|--------------|
| English | 🤩 | [English to Chinese](https://github.com/user-attachments/assets/127373bb-c152-4b7a-8d9d-e586b2c62b4b) | TODO |
| Russian | 😊 | [Russian to Chinese](https://github.com/user-attachments/assets/25264b5b-6931-4d39-948c-5a1e4ce42fa7) | TODO |
| French | 🤩 | [French to Japanese](https://github.com/user-attachments/assets/3ce068c7-9854-4c72-ae77-f2484c7c6630) | TODO |
| German | 🤩 | [German to Chinese](https://github.com/user-attachments/assets/07cb9d21-069e-4725-871d-c4d9701287a3) | TODO |
| Italian | 🤩 | [Italian to Chinese](https://github.com/user-attachments/assets/f1f893eb-dad3-4460-aaf6-10cac999195e) | TODO |
| Spanish | 🤩 | [Spanish to Chinese](https://github.com/user-attachments/assets/c1d28f1c-83d2-4f13-a1a1-859bd6cc3553) | TODO |
| Japanese | 😐 | [Japanese to Chinese](https://github.com/user-attachments/assets/856c3398-2da3-4e25-9c36-27ca2d1f68c2) | TODO |
| Chinese* | 🤩 | [Chinese to English](https://github.com/user-attachments/assets/48f746fe-96ff-47fd-bd23-59e9202b495c) | [Professor Luo Xiang's Talk Show](https://github.com/user-attachments/assets/85c64f8c-06cf-4af9-b153-ee9d2897b768) |
> *Chinese requires separate configuration of the whisperX model, see source code installation

Translation languages support all languages that the large language model can handle, while dubbing languages depend on the chosen TTS method.

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