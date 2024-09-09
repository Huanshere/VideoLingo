# 🏠 VideoLingo Local Deployment Guide (Windows)

VideoLingo offers multiple Whisper solutions for speech recognition text steps (as there's no single perfect choice currently). Choose one based on your personal configuration and needs.

| Solution | Advantages | Disadvantages |
|:---------|:-----------|:--------------|
| **whisper_timestamped** | • Runs locally<br>• Easy installation<br>• Uses native Whisper model | • Ideal for English only<br>• Requires GPU with 8GB+ VRAM |
| **whisperX** (🌟Recommended) | • Runs locally<br>• Based on faster-whisper, excellent performance<br>• Good multi-language support | • Requires CUDA and cuDNN installation<br>• Separate wav2vec model download for each language<br>• Requires GPU with 8GB+ VRAM |
| **whisperX_api** | • Uses Replicate API, no local computing power needed | • Replicate service may be unstable, occasional CUDA errors<br>• Uses large-v3, punctuation not as good as local v2 |

## 📋 Preparation

1. Register an account on [Yunwu API](https://api.wlai.vip/register?aff=TXMB) and recharge to get a token (or use any claude-3.5-sonnet provider)
   
   ![Yunwu API Registration Process](https://github.com/user-attachments/assets/762520c6-1283-4ba9-8676-16869fb94700)

2. If using `whisperX_api`, register a Replicate account, link a payment method, and get your token

## 🛠️ Installation Process

### Prerequisites

Before installing VideoLingo, ensure you complete the following steps:

1. Install [Visual Studio 2022](https://visualstudio.microsoft.com/thank-you-downloading-visual-studio/?sku=Community&channel=Release&version=VS2022&source=VSLandingPage&cid=2030&passive=false)
   - Select and install the "Desktop development with C++" component package

2. Install [CMake](https://github.com/Kitware/CMake/releases/download/v3.30.2/cmake-3.30.2-windows-x86_64.msi)

3. Install [Anaconda](https://www.anaconda.com/download/success)

4. Install [Git](https://git-scm.com/download/win)

5. For users choosing `whisperX`:
   - Install [Cuda Toolkit](https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe)
   - Install [Cudnn](https://developer.download.nvidia.com/compute/cudnn/9.3.0/local_installers/cudnn_9.3.0_windows.exe)
   - Restart your computer after installation

### Installation Steps

1. Open Anaconda Prompt and switch to the desktop directory:
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
   Choose the desired Whisper project when prompted, and the script will automatically install the corresponding torch and whisper versions.

5. 🎉 Launch the Streamlit application: Double-click `一键启动.bat` or enter
   ```bash
   streamlit run st.py
   ```
   Open the Web interface in your browser, select the corresponding Whisper method in the sidebar, and configure it.