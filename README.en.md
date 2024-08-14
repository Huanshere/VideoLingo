# 🌉 VideoLingo: Bridging Languages in Every Frame

![Python](https://img.shields.io/badge/python-v3.12-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![GitHub stars](https://img.shields.io/github/stars/Huanshere/VideoLingo.svg)

[中文](README.md) | [English](README.en.md)

🍖 Fully automated video localization: Seamlessly generate translated and dubbed videos from English video links!

QQ Group: 875297969

## 🌟 What We Offer

- 🎬 Netflix-quality subtitles: Say goodbye to amateur translations!

- 🎤 Clone your own voice for dubbing!

- ✨ Click-and-done in Streamlit!

> Check out our demo! 🚀💪

https://github.com/user-attachments/assets/0f5d5878-bfa5-41e4-ade1-d2b81d925a7d

> You can also use GPT-SoVITS to add your own voice!

https://github.com/user-attachments/assets/e9833df3-236c-46da-ba6c-a9636947c48b

## Features

- 📚 NLP and LLM-driven subtitle segmentation

- 🧠 Intelligent terminology knowledge base for context-aware translation

- 🔄 Three-step translation process: Direct translation - Reflection - Improvement

- 🎯 Precise word-level subtitle alignment

- 💰 Extremely low cost: Create 5 minutes of cross-language subtitles for just 0.1 yuan

- 🎤 High-quality personalized dubbing with GPT-SoVits

- 👨‍💻 Developer-friendly: Step-by-step structured files for easy customization: [English Guide](./docs/README_guide_en.md) | [Chinese Guide](./docs/README_guide_zh.md)

## Hardware Requirements

- Tested on Mac M1 Pro 16G and Windows RTX4060

## 🎯 How to Use

1. Download the one-click startup package: [Click here](https://pan.baidu.com/s/1bL2zorbs4OpzKC1Ctlh3JQ?pwd=6969) (Windows only, not widely tested. Mac users please install from source)

2. Configure the api_key in `config.py`

3. Click `OnekeyLaunch.bat` to start Streamlit!

<div style="display: flex; justify-content: space-around;">
  <img src="https://github.com/user-attachments/assets/4c41b498-574d-457b-80de-fefbede731e1" alt="Demo 1" width="45%" />
  <img src="https://github.com/user-attachments/assets/210ba9e6-1f8a-41d7-a8d5-d0d6fd96deea" alt="Demo 2" width="45%" />
</div>

## 🚀 Installation from Scratch

> **Note**: This installation guide is applicable for Mac and Windows systems

1. Clone the repository:
   ```bash
   git clone https://github.com/Huanshere/VideoLingo.git
   cd VideoLingo
   ```

2. Set up and activate the Conda virtual environment:
   ```bash
   conda create -n videolingo python=3.12.0
   conda activate videolingo
   ```

3. Configure `config.py`

4. Run the installation script:
   ```bash
   python install.py
   ```

5. 🎉 Launch Streamlit!
   ```bash
   streamlit run st.py
   ```

## 🙏 Acknowledgements

Thanks to the following open-source projects for their contributions:

- [whisper](https://github.com/openai/whisper): OpenAI's open-source automatic speech recognition system
- [whisper-timestamped](https://github.com/linto-ai/whisper-timestamped): Extension adding timestamp functionality to Whisper
- [yt-dlp](https://github.com/yt-dlp/yt-dlp): Command-line tool for downloading YouTube videos and content from other websites
- [GPT-SoVITS](https://github.com/RVC-Project/GPT-SoVITS) & [GPT-SoVITS-Inference](https://github.com/X-T-E-R/GPT-SoVITS-Inference): Speech synthesis system based on GPT and SoVITS, and its inference library
- [FFmpeg](https://github.com/FFmpeg/FFmpeg): Complete cross-platform solution for handling multimedia content
- [Ultimate Vocal Remover GUI v5 (UVR5)](https://github.com/Anjok07/ultimatevocalremovergui): Tool for separating vocals and instrumentals in music
- [json_repair](https://github.com/mangiucugna/json_repair): Super powerful library for repairing and parsing GPT's JSON output, seamlessly replacing json.loads

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo)