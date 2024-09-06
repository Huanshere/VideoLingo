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

- 🍖 Fully automated video translation tool, generating Netflix-quality subtitles in multiple languages!

- 🎤 Clone your own voice for dubbing! (🚧 Under development, temporarily offline)

- ✨ Click-and-done in Streamlit!

![demo.png](https://files.catbox.moe/clsmt9.png)

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

- Three-step translation process: Direct Translation - Reflection - Improvement

- Precise word-level subtitle alignment

- Create 5 minutes of Netflix-quality bilingual subtitles for just 1 yuan

- High-quality personalized dubbing with GPT-SoVits (🚧 Under development, may migrate to fish-speech)

- Developer-friendly: Structured step-by-step files for easy customization: [Chinese Technical Documentation](./docs/README_guide_zh.md) | [English Technical Documentation](./docs/README_guide_en.md) 
   > You can even execute each `step__.py` file under `core` individually!

## 🏠 Local Deployment

### Prerequisites

- **Register** and **recharge** at [Cloud Fog API](https://api.wlai.vip/register?aff=TXMB), then **apply for a token** (fill in the application as shown in the image)

- Copy this `api_key` to fill in the Streamlit webpage sidebar later

![image](https://github.com/user-attachments/assets/6e1b6fa8-f50a-4ac7-acb8-24d186645749)

### Method 1: One-click Installation Package (Windows Only)

1. Download and install the one-click installation package:
   - [Windows CPU Version](https://vip.123pan.cn/1817874751/7908462)
   - [Windows GPU Version](https://vip.123pan.cn/1817874751/7909068)

   Note: The **GPU version** requires additional software:
   - CMake: Download from [official website](https://cmake.org/download/)
   - Visual Studio: Download from [official website](https://visualstudio.microsoft.com/downloads/) (Check "Desktop development with C++" during installation)
   - Or download the above software from [this cloud drive link](https://www.123pan.com/s/2pDvjv-PnOPH)

2. Extract locally, double-click `一键启动.bat` (enter any email in the pop-up window), and the webpage will automatically open

### Method 2: Install from Source (Win or Mac)

1. Clone the repository:

   ```bash
   git clone https://github.com/Huanshere/VideoLingo.git
   cd VideoLingo
   ```

2. Set up and activate Conda virtual environment:

   ```bash
   conda create -n videolingo python=3.12.0
   conda activate videolingo
   ```

3. Run the installation script:

   ```bash
   python install.py
   ```

4. 🎉 Launch Streamlit and modify configurations in the web interface:
   ```bash
   streamlit run st.py
   ```

## ☁️ Cloud Experience

- This project has been uploaded to [Qudong Cloud-VideoLingo](https://open.virtaicloud.com/web/project/detail/480194078119297024) (v0.2 version), which can be quickly cloned and launched. Detailed tutorial with images [click here](docs/趋动云使用说明.md)

![qudongcloud.png](https://files.catbox.moe/ia9v1d.png)

## 🙏 Acknowledgements

Thanks to the contributions of the following open-source projects:

- [whisper](https://github.com/openai/whisper): OpenAI's open-source automatic speech recognition system
- [whisper-timestamped](https://github.com/linto-ai/whisper-timestamped): Extension adding timestamp functionality to Whisper
- [yt-dlp](https://github.com/yt-dlp/yt-dlp): Command-line tool for downloading YouTube videos and content from other websites
- [GPT-SoVITS](https://github.com/RVC-Project/GPT-SoVITS) & [GPT-SoVITS-Inference](https://github.com/X-T-E-R/GPT-SoVITS-Inference): Speech synthesis system and inference library based on GPT and SoVITS
- [FFmpeg](https://github.com/FFmpeg/FFmpeg): Complete cross-platform solution for handling multimedia content
- [Ultimate Vocal Remover GUI v5 (UVR5)](https://github.com/Anjok07/ultimatevocalremovergui): Tool for separating vocals and accompaniment in music
- [json_repair](https://github.com/mangiucugna/json_repair): Super powerful library for repairing and parsing GPT's JSON output, seamlessly replacing json.loads

## 🤝 Contributions Welcome

We welcome all forms of contributions, whether it's new features, bug fixes, or documentation improvements. If you have any ideas or suggestions, please feel free to open an issue or submit a pull request.

For further communication or assistance, welcome to join our QQ group

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo)