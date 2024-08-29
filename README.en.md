<div align="center">

# 🌉 VideoLingo: Connecting the World Frame by Frame

![Python](https://img.shields.io/badge/python-v3.12-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![GitHub stars](https://img.shields.io/github/stars/Huanshere/VideoLingo.svg)

[**中文**](README.md) | [**English**](README.en.md)

[**Bilibili Demo**](https://www.bilibili.com/video/BV1QsYXeGEPP/)

**QQ Group: 875297969**

</div>

## 🌟 What Can It Do

- 🍖 Fully automatic video translation, generating Netflix-quality subtitles!

- 🎤 Clone your own voice for dubbing! (🚧 Under development)

- ✨ Click-and-done in Streamlit!

![iqzp96.png](https://files.catbox.moe/iqzp96.png)

> Check out the results! 💪

<table>
<tr>
<td width="50%">

**Translated Subtitle Effect**

https://github.com/user-attachments/assets/0f5d5878-bfa5-41e4-ade1-d2b81d925a7d

</td>
<td width="50%">

**With Dubbing Effect**

https://github.com/user-attachments/assets/e9833df3-236c-46da-ba6c-a9636947c48b

</td>
</tr>
</table>

## ✨ Features

- Subtitle segmentation using NLP and LLM

- Intelligent terminology knowledge base for context-aware translation

- Three-step translation process: Direct translation - Reflection - Improvement

- Precise word-level subtitle alignment

- Create 5 minutes of Netflix-quality bilingual subtitles for just 1 yuan

- High-quality personalized dubbing with GPT-SoVits

- Developer-friendly: Step-by-step structured files for easy customization: [Chinese Technical Documentation](./docs/README_guide_zh.md) | [English Technical Documentation](./docs/README_guide_en.md)

## ⚡️ Quick Experience

- This project has been uploaded to [Qudong Cloud-VideoLingo](https://open.virtaicloud.com/web/project/detail/480194078119297024) for quick cloning and launching

- New registered users are gifted with 35 hours of free usage. Detailed tutorial with images [Click here](docs/趋动云使用说明.md)

![ia9v1d.png](https://files.catbox.moe/ia9v1d.png)

## 🏠 Local Deployment

> Supports Windows and Mac systems


> For Windows, before installing other dependencies, please make sure to download and install Visual Studio 2022 or Microsoft C++ Build Tools (smaller in size). Check and install the component package: "Desktop development with C++", execute the modification and wait for it to complete.
>
> Also install [Cmake build program](https://github.com/Kitware/CMake/releases/download/v3.30.2/cmake-3.30.2-windows-x86_64.msi)

1. Clone the repository:
> This step requires [git](https://git-scm.com/download/win) installed on your system

   ```bash
   git clone https://github.com/Huanshere/VideoLingo.git
   cd VideoLingo
   ```

2. Set up and activate Conda virtual environment:

> This step requires [Anaconda](https://www.anaconda.com/download/success) installed on your system
> 
> Enter the following commands in Anaconda powershell prompt:
   ```bash
   conda create -n videolingo python=3.12.0
   conda activate videolingo
   ```

3. Configure `config.py`

4. Run the installation script:

   ```bash
   python install.py
   ```

5. 🎉Launch Streamlit!
   ```bash
   streamlit run st.py
   ```

## 🙏 Acknowledgements

Thanks to the contributions of the following open-source projects:

- [whisper](https://github.com/openai/whisper): OpenAI's open-source automatic speech recognition system
- [whisper-timestamped](https://github.com/linto-ai/whisper-timestamped): Extension adding timestamp functionality to Whisper
- [yt-dlp](https://github.com/yt-dlp/yt-dlp): Command-line tool for downloading YouTube videos and content from other websites
- [GPT-SoVITS](https://github.com/RVC-Project/GPT-SoVITS) & [GPT-SoVITS-Inference](https://github.com/X-T-E-R/GPT-SoVITS-Inference): Speech synthesis system and inference library based on GPT and SoVITS
- [FFmpeg](https://github.com/FFmpeg/FFmpeg): Complete, cross-platform solution for processing multimedia content
- [Ultimate Vocal Remover GUI v5 (UVR5)](https://github.com/Anjok07/ultimatevocalremovergui): Tool for separating vocals and instrumentals in music
- [json_repair](https://github.com/mangiucugna/json_repair): Super powerful library for repairing and parsing GPT's JSON output, seamlessly replacing json.loads

## 🤝 Contributions Welcome

We welcome all forms of contributions, whether it's new features, bug fixes, or documentation improvements. If you have any ideas or suggestions, please feel free to open an issue or submit a pull request.

For further communication or assistance, welcome to join our QQ group

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo)
