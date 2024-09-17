# 🏠 VideoLingo Local Installation Guide

VideoLingo offers multiple Whisper solutions for the speech recognition text step. Choose one based on your personal configuration and needs.

| Solution | Advantages | Disadvantages |
|:---------|:-----------|:--------------|
| **whisper_timestamped** | • Runs locally<br>• Easy installation<br>• Uses native Whisper model | • Ideal for English only<br>• Requires GPU with 8GB+ VRAM |
| **whisperX**  | • Runs locally<br>• Based on faster-whisper, excellent performance<br>• Good multi-language support | • Requires CUDA and cuDNN installation<br>• Separate wav2vec model download for each language<br>• Requires GPU with 8GB+ VRAM |
| **whisperX_api** (🌟Recommended) | • Uses Replicate cloud computing, no local computing power needed | • Requires Visa card payment (about ¥0.1 per transcription) |

## 📋 API Preparation

1. Obtain the API_KEY for large language models:

| Model | Recommended Channel | Price | Effect |
|:------|:--------------------|:------|:-------|
| claude-3-5-sonnet | [Deepbricks](https://deepbricks.ai/api-key) | ¥50 / 1M (1/2 of official price) | 🤩 |
| TA/Qwen/Qwen1.5-72B-Chat | [OHMYGPT](https://www.ohmygpt.com?aff=u20olROA) | ¥3 / 1M | 😲 |
| deepseek-coder | [OHMYGPT](https://www.ohmygpt.com?aff=u20olROA) | ¥2 / 1M | 😲 |

   Note: Default is 3.5sonnet, 10-minute video translation costs about ¥3. Compatible with any OpenAI-Like model, but only these three are recommended, others may cause errors.

2. If using `whisperX_api`, prepare Replicate's Token:
   - Register on [Replicate](https://replicate.com/account/api-tokens), bind Visa card payment method, and obtain token
   - Or join QQ group to contact the author for free test tokens

## 💾 One-Click Package Tutorial

1. Download the `v0.8.0` one-click package (700M): [Direct Link](https://vip.123pan.cn/1817874751/8050534) | [Baidu Pan Backup](https://pan.baidu.com/s/1H_3PthZ3R3NsjS0vrymimg?pwd=ra64)

2. After extracting, double-click `OneKey.bat` in the folder

3. In the opened browser window, make necessary configurations in the sidebar, then create your video with one click!

> Note: Refer to the image at the bottom for the key configuration in the sidebar

## 🛠️ Source Code Installation Process

### Windows Prerequisites

Before installing the local Whisper version of VideoLingo, ensure at least **20GB** of free disk space and complete the following steps:

| Dependency | whisperX | whisper_timestamped | whisperX_api |
|:-----------|:---------|:--------------------|:-------------|
| [Anaconda](https://www.anaconda.com/download/success)<br>*Check "Add to PATH"* | ✅ | ✅ | ✅ |
| [Git](https://git-scm.com/download/win) | ✅ | ✅ | ✅ |
| [Cuda Toolkit 12.6](https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe) | ✅ | | |
| [Cudnn 9.3.0](https://developer.download.nvidia.com/compute/cudnn/9.3.0/local_installers/cudnn_9.3.0_windows.exe) | ✅ | | |
| [Visual Studio 2022](https://visualstudio.microsoft.com/zh-hans/thank-you-downloading-visual-studio/?sku=Community&channel=Release&version=VS2022&source=VSLandingPage&cid=2030&passive=false)<br>*Check "Desktop development with C++"* | | ✅ | |
| [CMake](https://github.com/Kitware/CMake/releases/download/v3.30.2/cmake-3.30.2-windows-x86_64.msi) | | ✅ | |

> Note:
> - Restart your computer after installation
> - If you encounter CUDA Memory errors when running whisperX, please manually reduce the batch size in `core/all_whisper_methods/whisperX.py` and try again

### Installation Steps
Supports Win, Mac, Linux. If you encounter any issues, you can ask GPT about the entire process~
1. Open Anaconda Powershell Prompt and switch to the desktop directory:
   ```bash
   cd desktop
   ```

2. Clone the project:
   ```bash
   git clone https://github.com/Huanshere/VideoLingo.git
   cd VideoLingo
   ```

3. Configure virtual environment:
   ```bash
   conda create -n videolingo python=3.10.0
   conda activate videolingo
   ```

4. Run the installation script:
   ```bash
   python install.py
   ```
   Choose the desired Whisper project when prompted, the script will automatically install the corresponding torch and whisper versions

   Note: Mac users need to manually install ffmpeg as prompted

5. 🎉 Launch the Streamlit application:
   ```bash
   streamlit run st.py
   ```

6. Set the key in the sidebar of the pop-up webpage, and make sure to select the correct Whisper method to use

   ![settings](https://github.com/user-attachments/assets/3d99cf63-ab89-404c-ae61-5a8a3b27d840)