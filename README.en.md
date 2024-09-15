<div align="center">

# 🌉 VideoLingo: Connecting the World, Frame by Frame

![Python](https://img.shields.io/badge/python-v3.12-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![GitHub stars](https://img.shields.io/github/stars/Huanshere/VideoLingo.svg)

[**中文**](README.md) | [**English**](README.en.md)

[**Bilibili Demo**](https://www.bilibili.com/video/BV1QsYXeGEPP/)

**QQ Group: 875297969**

</div>

## 🌟 What Can It Do

- 🍖 Fully automated video translation, generating Netflix-quality subtitles!

- 🎤 Clone your own voice for dubbing! (🚧 Still in development)

- ✨ Click-and-done in Streamlit!

> Check out the results! 💪

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

## ✨ Features

- Subtitle segmentation using NLP and LLM

- Intelligent terminology knowledge base for context-aware translation

- Three-step translation process: Direct Translation - Reflection - Improvement

- Precise word-level subtitle alignment

- Create 5 minutes of Netflix-quality bilingual subtitles for just 1 yuan

- Developer-friendly: Step-by-step structured files for easy customization: [Chinese Technical Documentation](./docs/README_guide_zh.md) | [English Technical Documentation](./docs/README_guide_en.md) 
    > You can even run each `step__.py` file under `core` individually!   

## 🏠 [Local Deployment Guide](./docs/install_locally_en.md)

## 🚧 Current Limitations

We are continuously improving VideoLingo, but there are still some limitations:

- Audio Length: Currently only supports videos up to 30 minutes, we plan to extend this limit soon.

- Input Language Support:

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

😖 Whisper has difficulty providing punctuation when recognizing Chinese word-level timelines.

- Output Language Support: VideoLingo supports translation into all languages that Claude can handle

## 🙏 Acknowledgements

Thanks to the following open-source projects for their contributions:

- [whisper](https://github.com/openai/whisper): OpenAI's open-source automatic speech recognition system
- [whisper-timestamped](https://github.com/linto-ai/whisper-timestamped): Extension adding timestamp functionality to Whisper
- [whisperX](https://github.com/m-bain/whisperX): Extension adding timestamp functionality to Whisper
- [yt-dlp](https://github.com/yt-dlp/yt-dlp): Command-line tool for downloading YouTube videos and content from other websites
- [GPT-SoVITS](https://github.com/RVC-Project/GPT-SoVITS) & [GPT-SoVITS-Inference](https://github.com/X-T-E-R/GPT-SoVITS-Inference): Speech synthesis system and inference library based on GPT and SoVITS
- [FFmpeg](https://github.com/FFmpeg/FFmpeg): Complete, cross-platform solution for handling multimedia content
- [Ultimate Vocal Remover GUI v5 (UVR5)](https://github.com/Anjok07/ultimatevocalremovergui): Tool for separating vocals and instrumentals in music
- [json_repair](https://github.com/mangiucugna/json_repair): Super powerful library for repairing and parsing GPT's JSON output, seamlessly replacing json.loads

## 🤝 Contributions Welcome

We welcome all forms of contributions. If you have any ideas or suggestions, please feel free to raise an issue or submit a pull request.

For further communication or assistance, welcome to join our QQ group.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo)