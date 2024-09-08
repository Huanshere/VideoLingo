# 🏠 VideoLingo Local Deployment Guide (Windows)

VideoLingo offers a choice of multiple Whisper solutions (as there is no single perfect option so far):

| Solution | Advantages | Disadvantages |
|:---------|:-----------|:--------------|
| **whisper_timestamped** | • Runs locally<br>• Easy to install<br>• Uses native Whisper model | • Ideal for English only |
| **whisperX_api** | • Uses Replicate API, no local computing power needed | • Replicate service may be unstable<br>• Occasional CUDA errors |
| **whisperX** (🌟Recommended) | • Runs locally<br>• Based on faster-whisper, excellent performance | • Requires CUDA and cuDNN configuration<br>• Separate wav2vec model download for each language |

## 📋 Preparation

1. Register an account on [Cloud Fog API](https://api.wlai.vip/register?aff=TXMB) and recharge to get a token
   
   ![Cloud Fog API Registration Process](https://github.com/user-attachments/assets/762520c6-1283-4ba9-8676-16869fb94700)

2. If using `whisperX_api`, please register a Replicate account and bind a payment method

## 🛠️ Installation Process

### Prerequisites

Before installing VideoLingo, please ensure you complete the following steps (most of which are for GPU acceleration):

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

1. Clone the project:
   ```bash
   git clone https://github.com/Huanshere/VideoLingo.git
   cd VideoLingo
   ```

2. Configure virtual environment:
   ```bash
   conda create -n videolingo python=3.12.0
   conda activate videolingo
   ```

3. Run the installation script:
   ```bash
   python install.py
   ```
   Follow the prompts to select the desired Whisper project, and the script will automatically install the corresponding torch and whisper versions.

4. 🎉 Launch the Streamlit application:
   ```bash
   streamlit run st.py
   ```
   Open the Web interface in your browser, select the corresponding Whisper method through the sidebar and configure it.