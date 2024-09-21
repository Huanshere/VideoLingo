# 🏠 VideoLingo Installation Guide

This project requires the use of large language models, WhisperX, and TTS. Multiple options are provided for each component. **Please read the installation guide carefully 😊**

## 📋 API Preparation

### 1. **Obtain API_KEY for large language models**:

| Model | Recommended Provider | base_url | Price | Effect |
|:------|:---------------------|:---------|:------|:-------|
| claude-3-5-sonnet-20240620 | [Yunwu API](https://yunwu.zeabur.app/register?aff=TXMB) | https://yunwu.zeabur.app | $2.14 / 1M | 🤩 |
| Qwen/Qwen2.5-72B-Instruct | [Silicon Flow](https://cloud.siliconflow.cn/i/ttKDEsxE) | https://api.siliconflow.cn | $0.57 / 1M | 😲 |
> Note: Yunwu API also supports OpenAI's tts-1 interface, which can be used in the dubbing step

#### Common Questions

<details>
<summary>How to choose a model?</summary>

- 🚀 By default, Qwen2.5 is used, costing about $0.43 for 1h video translation.
- 🌟 Claude 3.5 has better results, with excellent translation coherence and no AI flavor, but it's more expensive.
</details>

<details>
<summary>How to get an API key?</summary>

1. Click the link for the recommended provider above
2. Register an account and top up
3. Create a new key on the API key page
</details>

<details>
<summary>Can I use other models?</summary>

- ✅ OAI-Like API interfaces are supported, but you need to change it in the Streamlit sidebar.
- ⚠️ However, other models have weak ability to follow instructions and are very likely to cause errors during translation, so they are strongly discouraged.
</details>

### 2. **Prepare Replicate's Token** (Only when using whisperX ☁️ on Replicate)

VideoLingo uses WhisperX for speech recognition, supporting both local deployment and cloud API. The API version is recommended, and an integrated package for the API version is provided below.
#### Solution Comparison:
| Solution | Disadvantages |
|:---------|:--------------|
| **whisperX 🖥️** | • Install CUDA 🛠️<br>• Download models 📥<br>• High VRAM requirement 💾 |
| **whisperX ☁️ (Recommended)** | • Requires VPN 🕵️‍♂️<br>• Visa card 💳 |

#### Obtaining the Token
   - Register on [Replicate](https://replicate.com/account/api-tokens), bind a Visa card payment method, and obtain the token
   - Or join the QQ group to get free test tokens from the group announcement

### 3. **TTS API**
VideoLingo provides multiple TTS integration methods. Here's a comparison (skip if you're only translating without dubbing):

| TTS Solution | Advantages | Disadvantages | Chinese Effect | Non-Chinese Effect |
|:-------------|:-----------|:--------------|:---------------|:-------------------|
| 🎙️ OpenAI TTS | High quality, realistic emotion | Chinese sounds like a foreigner | 😕 | 🤩 |
| 🎤 Edge TTS | Free | Overused | 😊 | 😊 |
| 🔊 Azure TTS (Recommended) | Natural Chinese effect | Inconvenient to top up | 🤩 | 😃 |
| 🗣️ GPT-SoVITS (beta) | Local, cloning, unbeatable in Chinese | Currently only supports English input Chinese output, requires GPU for model training, best for single-person videos without obvious BGM, and the base model should be close to the original voice | 😱 | 🚫 |

For OpenAI TTS, [Yunwu API](https://yunwu.zeabur.app/register?aff=TXMB) is recommended.
Edge TTS requires no configuration, for Azure TTS please register on the official website to get the key. Configure these in the sidebar of the VideoLingo running webpage later.

<details>
<summary>Using GPT-SoVITS (only supports v2 new version)</summary>

1. Please refer to the [official Yuque document](https://www.yuque.com/baicaigongchang1145haoyuangong/ib3g1e/dkxgpiy9zb96hob4#KTvnO) for configuration requirements and to download the integrated package.

2. Place `GPT-SoVITS-v2-xxx` in the same directory level as `VideoLingo`.

3. Choose one of the following methods to configure the model:

   a. Using a self-trained model:
   - Copy `tts_infer.yaml` from `GPT-SoVITS-v2-xxx\GPT_SoVITS\configs` and rename it to `your_preferred_character_name.yaml`.
   - In the sidebar of the VideoLingo webpage, set `GPT-SoVITS Character` to `your_preferred_character_name`.

   b. Using a pre-trained model:
   - Download my model from [here](https://vip.123pan.cn/1817874751/8117662), extract and overwrite to `GPT-SoVITS-v2-xxx`.
   - Set `GPT-SoVITS Character` to `Huanyuv2`.

   c. Using other trained models:
   - Place the model files in `GPT_weights_v2` and `SoVITS_weights_v2` respectively.
   - Refer to method a, rename and modify the paths in `tts_infer.yaml` to point to your two models.

After configuration, VideoLingo will automatically open the inference API port of GPT-SoVITS in the pop-up command line during the dubbing step. You can manually close it after dubbing is complete.
</details>


## 🚀 whisperX ☁️ Integrated Package
> Note: Due to technical reasons, the integrated package cannot use edge-tts for dubbing. The CPU version of torch is slow when using UVR5 denoising in the dubbing step. If you need to use the GPU version of torch, please install from source code.

1. Download the `v1.0.0` one-click package (750M): [CPU Version Download](https://vip.123pan.cn/1817874751/8117948) | [Baidu Backup](https://pan.baidu.com/s/1H_3PthZ3R3NsjS0vrymimg?pwd=ra64)

2. After extracting, double-click `OneKeyStart.bat` in the folder

3. In the opened browser window, make necessary configurations in the sidebar, then create your video with one click!
  ![settings](https://github.com/user-attachments/assets/3d99cf63-ab89-404c-ae61-5a8a3b27d840)

## 🛠️ Source Code Installation Process

### Windows Prerequisites

Before installing VideoLingo, ensure you have **20G** of free disk space and complete the following steps:

| Dependency | whisperX 🖥️ | whisperX ☁️ |
|:-----------|:------------|:------------|
| Miniconda 🐍 | [Download](https://docs.conda.io/en/latest/miniconda.html) | [Download](https://docs.conda.io/en/latest/miniconda.html) |
| Git 🌿 | [Download](https://git-scm.com/download/win) | [Download](https://git-scm.com/download/win) |
| Cuda Toolkit 12.6 🚀 | [Download](https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe) | - |
| Cudnn 9.3.0 🧠 | [Download](https://developer.download.nvidia.com/compute/cudnn/9.3.0/local_installers/cudnn_9.3.0_windows.exe) | - |

> Note: Check "Add to system Path" when installing Miniconda, restart your computer after installation 🔄

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

5. 🎉 Enter the command or click `OneKeyStart.bat` to launch the Streamlit application:
   ```bash
   streamlit run st.py
   ```

6. Set the key in the sidebar of the pop-up webpage, and make sure to select the correct Whisper method to use

   ![settings](https://github.com/user-attachments/assets/3d99cf63-ab89-404c-ae61-5a8a3b27d840)