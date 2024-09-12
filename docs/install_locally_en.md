# 🏠 VideoLingo Local Deployment Guide

VideoLingo offers multiple Whisper solutions for the speech recognition text step (as there's no single perfect choice currently). Choose one based on your personal configuration and needs.

| Solution | Advantages | Disadvantages |
|:---------|:-----------|:--------------|
| **whisper_timestamped** | • Runs locally<br>• Easy installation<br>• Uses native Whisper model | • Ideal for English only<br>• Requires GPU with 8GB+ VRAM |
| **whisperX**  | • Runs locally<br>• Based on faster-whisper, excellent performance<br>• Good multi-language support | • Requires CUDA and cuDNN installation<br>• Separate wav2vec model download for each language<br>• Requires GPU with 8GB+ VRAM |
| **whisperX_api** (🌟Recommended) | • Uses Replicate API, no local computing power needed | • Replicate service may be unstable, occasional CUDA errors<br>• large-v3 model used may have inferior punctuation compared to v2 |

## 📋 Preparation

1. Obtain the `API_KEY` for `claude-3-5-sonnet`. Recommended affordable channel: [Yunwu API](https://api2.wlai.vip/register?aff=TXMB), only ¥35/1M, 1/3 of the official price. Of course, you can also use other API providers, but it's recommended to choose `claude-3-5-sonnet` > `Qwen 1.5 72B Chat` > `deepseek-coder`
 
   ![yunwu](https://github.com/user-attachments/assets/7aabfa87-06b5-4004-8d9e-fa4a0743a912)

2. If using `whisperX_api`, please register and set up payment method on the [Replicate official website](https://replicate.com/account/api-tokens) to obtain your token. You can also contact me in the QQ group for free test tokens.

## 💾 One-Click Package Download

If you don't want to install manually, we also provide a one-click installation package for the `whisperX_api` version:

1. Download the `v0.6.0` one-click installation package (600M): [Direct Link](https://vip.123pan.cn/1817874751/7960342) | [Baidu Pan Backup](https://pan.baidu.com/s/16nV3ccnGCjASzYlLnMRP_Q?pwd=6969)

2. Extract the downloaded file to your desired location

3. Double-click `一键启动.bat` in the extracted folder

4. In the opened browser window, follow the interface prompts for configuration and usage

> Note: Refer to the image at the bottom for the key configuration process in the web interface

## 🛠️ Manual Installation Process (Windows)

### Prerequisites

Before installing VideoLingo, ensure at least **20GB** of free disk space and complete the following steps:

1. Install [Anaconda](https://www.anaconda.com/download/success)
   - Make sure to check "Add to PATH" during installation

2. Install [Git](https://git-scm.com/download/win)

3. For `whisperX` users:
   - Install [Cuda Toolkit](https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe)
   - Install [Cudnn](https://developer.download.nvidia.com/compute/cudnn/9.3.0/local_installers/cudnn_9.3.0_windows.exe)
   - Restart your computer after installation
   > tip: If you encounter CUDA Memory errors during subsequent runs, please manually reduce the batch size in `core/all_whisper_methods/whisperX.py` and try again

4. For `whisper_timestamped` users:
   - Install [Visual Studio 2022](https://visualstudio.microsoft.com/zh-hans/thank-you-downloading-visual-studio/?sku=Community&channel=Release&version=VS2022&source=VSLandingPage&cid=2030&passive=false)
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
   Choose the desired Whisper project when prompted, the script will automatically install the corresponding torch and whisper versions

   Ensure network connection and check for any errors during the installation process

5. 🎉 Launch the Streamlit application:
   ```bash
   streamlit run st.py
   ```

6. Set the key in the sidebar of the pop-up webpage, and make sure to select the correct Whisper method to use

   ![2](https://github.com/user-attachments/assets/ba5621f0-8320-4a45-8da8-9ea574b5c7cc)


## Docker Deployment

Pull Image

```bash
docker pull sguann/videolingo_app:latest
```

Run Image：
```bash
docker run -d -p 8501:8501 -e API_KEY=xxx -e BASE_URL=xxx -e WHISPER_METHOD=xxx -e DISPLAY_LANGUAGE=xxx sguann/videolingo_app:latest
```

Where:

 - `API_KEY`: Access token, needs to be applied for by yourself. Recommended: [YunWu API](https://api2.wlai.vip/register?aff=TXMB)
 - `BASE_URL`: API provider interface, no need for v1 suffix
 - `WHISPER_METHOD`: Whisper model, options are: `whisper_timestamped`, `whisperX`, `whisperX_api`, default is `whisperX_api`
 - `DISPLAY_LANGUAGE`: Display language, options are `zh_CN`, `zh_TW`, `en_US`, `ja_JP`, default is `auto`
