# 🏠 VideoLingo Local Deployment Guide (Windows)

VideoLingo offers multiple Whisper solutions for speech recognition (as there's no single perfect choice currently). Choose one based on your personal configuration and needs.

| Solution | Advantages | Disadvantages |
|:---------|:-----------|:--------------|
| **whisper_timestamped** | • Runs locally<br>• Easy installation<br>• Uses native Whisper model | • Ideal for English only<br>• Requires GPU with 8GB+ VRAM |
| **whisperX**  | • Runs locally<br>• Based on faster-whisper, excellent performance<br>• Good multi-language support | • Requires CUDA and cuDNN installation<br>• Separate wav2vec model download for each language<br>• Requires GPU with 8GB+ VRAM |
| **whisperX_api** (🌟Recommended) | • Uses Replicate API, no local computing power needed | • Replicate service may be unstable, occasional CUDA errors<br>• large-v3 model used may have inferior punctuation compared to v2 |

## 📋 Preparation

1. Register an account on [Yunwu API](https://api.wlai.vip/register?aff=TXMB) and recharge to get a token (or use any claude-3.5-sonnet provider)
   > For best results, choose claude-3.5-sonnet. For testing, you can also select deepseek-coder, configure it later in the sidebar
   
   ![Yunwu API Registration Process](https://github.com/user-attachments/assets/762520c6-1283-4ba9-8676-16869fb94700)

2. If using `whisperX_api`, register a Replicate account, set up payment method, and obtain your token. You can also contact me for a free key for testing.

## 💾 One-Click Package Download

If you don't want to install manually, we also provide a one-click installation package for the `whisperX_api` version:

1. Download the `v0.6.0` one-click installation package (600M): [Direct Link](https://your-download-link-here.com) | [Baidu Pan Backup](https://pan.baidu.com/s/16nV3ccnGCjASzYlLnMRP_Q?pwd=6969)

2. Extract the downloaded file to your desired location

3. Double-click `一键启动.bat` in the extracted folder

4. In the opened browser window, follow the interface prompts for configuration and usage

> Note: The one-click package includes all necessary dependencies, no additional installation required. However, you still need to prepare API keys to use all features. Refer to the bottom for the key configuration process in the web interface.

## 🛠️ Manual Installation Process

### Prerequisites

Before installing VideoLingo, ensure at least **20GB** of free disk space and complete the following steps:

1. Install [Anaconda](https://www.anaconda.com/download/success)
   - Make sure to check "Add to PATH" during installation

2. Install [Git](https://git-scm.com/download/win)

3. For `whisperX` users:
   - Install [Cuda Toolkit](https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe)
   - Install [Cudnn](https://developer.download.nvidia.com/compute/cudnn/9.3.0/local_installers/cudnn_9.3.0_windows.exe)
   - Restart your computer after installation

4. For `whisper_timestamped` users:
   - Install [Visual Studio 2022](https://visualstudio.microsoft.com/thank-you-downloading-visual-studio/?sku=Community&channel=Release&version=VS2022&source=VSLandingPage&cid=2030&passive=false)
     - Check "Desktop development with C++" component package in the installation interface
   - Install [CMake](https://github.com/Kitware/CMake/releases/download/v3.30.2/cmake-3.30.2-windows-x86_64.msi)

### Installation Steps
> If you encounter any issues, you can ask GPT about the entire process~
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
   Choose the desired Whisper project when prompted, the script will automatically install the corresponding torch and whisper versions.

5. 🎉 Launch the Streamlit application:
   ```bash
   streamlit run st.py
   ```
   Open the Web interface in your browser, select the corresponding Whisper method in the sidebar and configure it.

6. Set the key in the sidebar of the pop-up webpage, and make sure to select the correct Whisper method to use

   ![2](https://github.com/user-attachments/assets/ba5621f0-8320-4a45-8da8-9ea574b5c7cc)