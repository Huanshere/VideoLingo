# 🏠 VideoLingo Installation Guide

## Whisper Model Selection
VideoLingo offers multiple Whisper solutions for the speech recognition text step. It is recommended to use the one-click package for the whisperX_api version.

| Solution | Advantages | Disadvantages |
|:---------|:-----------|:--------------|
| **whisper_timestamped** | • Runs locally<br>• Easy installation<br>• Uses native Whisper model | • Ideal for English only<br>• Requires GPU with 8GB+ VRAM |
| **whisperX**  | • Runs locally<br>• Based on faster-whisper, excellent performance<br>• Good multi-language support | • Requires CUDA and cuDNN installation<br>• Separate wav2vec model download for each language<br>• Requires GPU with 8GB+ VRAM |
| **whisperX_api** <br> (🌟Recommended, one-click package available) | • Uses Replicate cloud computing, no local computing power needed | • Requires stable VPN (preferably US node) |

## 📋 API Preparation

1. Obtain the API_KEY for large language models:

| Model | Recommended Provider | base_url | Price | Effect |
|:------|:---------------------|:---------|:------|:-------|
| claude-3-5-sonnet-20240620 | [yunwu API](https://yunwu.zeabur.app/register?aff=TXMB) | https://yunwu.zeabur.app | $2.14 / 1M | 🤩 |
| Qwen/Qwen2.5-72B-Instruct | [Silicon Flow](https://cloud.siliconflow.cn/i/ttKDEsxE) | https://api.siliconflow.cn | $0.57 / 1M | 😲 |

<details>
<summary><strong>How to choose a model?</strong></summary>
<p>By default, Qwen2.5 is used, costing about $0.43 for 1h video translation. Claude 3.5 has better results, with excellent translation coherence and no AI flavor, but it's more expensive.</p>
</details>
<details>
<summary><strong>How to get an API key?</strong></summary>
<p>Register and top up with any large model provider, then create a new key on the API key page.</p>
</details>
<details>
<summary><strong>Can I use other models?</strong></summary>
<p>OAI-Like API interfaces are supported, but you need to change it in the Streamlit sidebar. However, other models have weak ability to follow instructions and are very likely to cause errors during translation, so they are strongly discouraged.</p>
</details>

2. If using `whisperX_api`, prepare Replicate's Token:
   - Register on [Replicate](https://replicate.com/account/api-tokens), bind Visa card payment method, and obtain token
   - Or join QQ group to get free test tokens from the group announcement

## 💾 whisperX_api Version One-Click Package Tutorial

1. Download the `v0.8.2` one-click package (700M): [Direct Link](https://vip.123pan.cn/1817874751/8099913) | [Baidu Pan Backup](https://pan.baidu.com/s/1H_3PthZ3R3NsjS0vrymimg?pwd=ra64)

2. After extracting, double-click `OneKey.bat` in the folder

3. In the opened browser window, make necessary configurations in the sidebar, then create your video with one click!
  ![settings](https://github.com/user-attachments/assets/3d99cf63-ab89-404c-ae61-5a8a3b27d840)

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

> Note: Restart your computer after installation

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

3. Configure virtual environment (must be 3.10.0):
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