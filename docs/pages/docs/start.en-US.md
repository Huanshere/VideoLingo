
# 🚀 Getting Started

## 📋 API Preparation
This project requires the use of large language models, WhisperX, and TTS. Multiple options are provided for each component. **Please read the configuration guide carefully 😊**
### 1. **Obtain API_KEY for Large Language Models**:

| Recommended Model | Recommended Provider | base_url | Price | Effect |
|:-----|:---------|:---------|:-----|:---------|
| claude-3-5-sonnet-20240620 (default) | [Yunwu API](https://yunwu.zeabur.app/register?aff=TXMB) | https://yunwu.zeabur.app | ¥15 / 1M tokens (1/10 of official price) | 🤩 |

⚠️ Warning: The prompt involves multi-step thinking chains and complex JSON formats. Models other than Claude 3.5 Sonnet are prone to errors. The cost for a one-hour video is about ¥7.

> Note: Yunwu API also supports OpenAI's tts-1 interface, which can be used in the dubbing step.

<details>
<summary>How to get an API key from Yunwu API?</summary>

1. Click the link for the recommended provider above
2. Register an account and recharge
3. Create a new API key on the API key page
4. For Yunwu API, make sure to check `Unlimited Quota`, select the `claude-3-5-sonnet-20240620` model, and it is recommended to choose the `Pure AZ 1.5x` channel. If you need to use OpenAI for dubbing, also check the `tts-1` model
</details>

<details>
<summary>Can I use other models?</summary>

- ✅ Supports OAI-Like API interfaces, but you need to change it yourself in the Streamlit sidebar.
- ⚠️ However, other models (especially small models) have weak ability to follow instructions and are very likely to report errors during translation, which is strongly discouraged.
</details>

### 2. **Prepare Replicate Token** (Only when using whisperXapi ☁️)

VideoLingo uses WhisperX for speech recognition, supporting both local deployment and cloud API. If you don't have a GPU or just want to quickly experience it, you can use the cloud API and the one-click easy package.

#### Comparison of options:
| Option | Disadvantages |
|:-----|:-----|
| **whisperX 🖥️** | • Install CUDA 🛠️<br>• Download model 📥<br>• High VRAM requirement 💾 |
| **whisperXapi ☁️** | • Requires VPN 🕵️‍♂️<br>• Visa card 💳<br>• **Poor Chinese effect** 🚫 |

<details>
<summary>How to obtain the token</summary>
Register at [Replicate](https://replicate.com/account/api-tokens), bind a Visa card payment method, and obtain the token. **Or join the QQ group to get a free test token from the group announcement**
</details>

### 3. **TTS API**
VideoLingo provides multiple TTS integration methods. Here's a comparison (skip this if you're only translating without dubbing):

| TTS Option | Advantages | Disadvantages | Chinese Effect | Non-Chinese Effect |
|:---------|:-----|:-----|:---------|:-----------|
| 🎙️ OpenAI TTS | Realistic emotion | Chinese sounds like a foreigner | 😕 | 🤩 |
| 🔊 Azure TTS (Recommended) | Natural effect | Inconvenient recharge | 🤩 | 😃 |
| 🎤 Fish TTS  | Sounds like a real local | Limited official models | 😂 | 😂 |
| 🗣️ GPT-SoVITS (Testing) | Strongest voice cloning | Currently only supports Chinese and English, requires GPU for model inference, configuration requires relevant knowledge | 🏆 | 🚫 |

- For OpenAI TTS, we recommend using [Yunwu API](https://yunwu.zeabur.app/register?aff=TXMB), make sure to check the `tts-1` model;
- **Azure TTS test keys can be obtained in the QQ group announcement** or you can register and recharge yourself on the [official website](https://learn.microsoft.com/zh-cn/azure/ai-services/speech-service/get-started-text-to-speech?tabs=windows%2Cterminal&pivots=programming-language-python);
- For Fish TTS, please register yourself on the [official website](https://fish.audio/zh-CN/go-api/) (10 USD free credit)

<details>
<summary>How to choose an OpenAI voice?</summary>

You can find the voice list on the [official website](https://platform.openai.com/docs/guides/text-to-speech/voice-options), such as `alloy`, `echo`, `nova`, etc. Modify `openai_tts.voice` in `config.yaml` to change the voice.

</details>

<details>
<summary>How to choose an Azure voice?</summary>

It is recommended to listen and choose the voice you want in the [online experience](https://speech.microsoft.com/portal/voicegallery), and find the corresponding code for that voice in the right-hand code, such as `zh-CN-XiaoxiaoMultilingualNeural`

</details>

<details>
<summary>How to choose a Fish TTS voice?</summary>

Go to the [official website](https://fish.audio) to listen and choose the voice you want, and find the corresponding code for that voice in the URL, such as Ding Zhen is `54a5170264694bfc8e9ad98df7bd89c3`. Popular voices have been added to `config.yaml`. If you need to use other voices, please modify the `fish_tts.character_id_dict` dictionary in `config.yaml`.

</details>

<details>
<summary>GPT-SoVITS-v2 Usage Tutorial</summary>

1. Go to the [official Yuque document](https://www.yuque.com/baicaigongchang1145haoyuangong/ib3g1e/dkxgpiy9zb96hob4#KTvnO) to check the configuration requirements and download the integrated package.

2. Place `GPT-SoVITS-v2-xxx` in the same directory level as `VideoLingo`. **Note that they should be parallel folders.**

3. Choose one of the following methods to configure the model:

   a. Self-trained model:
   - After training the model, `tts_infer.yaml` under `GPT-SoVITS-v2-xxx\GPT_SoVITS\configs` will automatically be filled with your model address. Copy and rename it to `your_preferred_english_character_name.yaml`
   - In the same directory as the `yaml` file, place the reference audio you'll use later, named `your_preferred_english_character_name_text_content_of_reference_audio.wav` or `.mp3`, for example `Huanyuv2_Hello, this is a test audio.wav`
   - In the sidebar of the VideoLingo webpage, set `GPT-SoVITS Character` to `your_preferred_english_character_name`.

   b. Use pre-trained model:
   - Download my model from [here](https://vip.123pan.cn/1817874751/8137723), extract and overwrite to `GPT-SoVITS-v2-xxx`.
   - Set `GPT-SoVITS Character` to `Huanyuv2`.

   c. Use other trained models:
   - Place the `xxx.ckpt` model file in the `GPT_weights_v2` folder and the `xxx.pth` model file in the `SoVITS_weights_v2` folder.
   - Refer to method a, rename the `tts_infer.yaml` file and modify the `t2s_weights_path` and `vits_weights_path` in the `custom` section of the file to point to your models, for example:
  
      ```yaml
      # Example configuration for method b:
      t2s_weights_path: GPT_weights_v2/Huanyu_v2-e10.ckpt
      version: v2
      vits_weights_path: SoVITS_weights_v2/Huanyu_v2_e10_s150.pth
      ```
   - Refer to method a, place the reference audio you'll use later in the same directory as the `yaml` file, named `your_preferred_english_character_name_text_content_of_reference_audio.wav` or `.mp3`, for example `Huanyuv2_Hello, this is a test audio.wav`. The program will automatically recognize and use it.
   - ⚠️ Warning: **Please use English to name the `character_name`**, otherwise errors will occur. The `text_content_of_reference_audio` can be in Chinese. It's still in beta version and may produce errors.


   ```
   # Expected directory structure:
   .
   ├── VideoLingo
   │   └── ...
   └── GPT-SoVITS-v2-xxx
       ├── GPT_SoVITS
       │   └── configs
       │       ├── tts_infer.yaml
       │       ├── your_preferred_english_character_name.yaml
       │       └── your_preferred_english_character_name_text_content_of_reference_audio.wav
       ├── GPT_weights_v2
       │   └── [Your GPT model file]
       └── SoVITS_weights_v2
           └── [Your SoVITS model file]
   ```
        
After configuration, make sure to select `Reference Audio Mode` in the webpage sidebar (for detailed principles, please refer to the Yuque document). During the dubbing step, VideoLingo will automatically open the inference API port of GPT-SoVITS in the pop-up command line. You can manually close it after dubbing is complete. Note that the stability of this method depends on the chosen base model.</details>

## 💨 Windows One-Click Package

### Important Note:

**The one-click package does not have all the features of a source code installation**. It's primarily for quick testing (we now recommend using the Colab version for trials). For processing long videos and accessing full functionality, we strongly advise using the source code installation. Here's a comparison:

| One-Click Package | Source Code Installation |
|-------------------|--------------------------|
| 💻 CPU version of torch, about **2.7GB** | 🖥️ Requires Nvidia GPU and **25GB** disk space |
| 🐢 UVR5 voice separation is slow on CPU | 🚀 GPU-accelerated UVR5 |
| ☁️ Only supports whisperXapi, no local whisperX | 🏠 Supports local whisperX |
| 🈚 No Chinese transcription support | 🈶 Supports Chinese transcription |
| 🎵 No voice separation in transcription, not suitable for videos with noisy BGM | 🎼 Can process videos with noisy background music |

### Download and Usage Instructions

1. Download the `v1.5` one-click package (800MB): [Direct Download](https://vip.123pan.cn/1817874751/8313069) | [Baidu Backup](https://pan.baidu.com/s/1H_3PthZ3R3NsjS0vrymimg?pwd=ra64)

2. After extracting, double-click `一键启动.bat` (One-click Start) in the folder

3. In the browser window that opens, make necessary configurations in the sidebar, then click to produce your video!
  ![attention](https://github.com/user-attachments/assets/9ff9d8e1-5422-466f-9e28-1803f23afdc7)

## 🛠️ Source Code Installation Process

### Windows Prerequisites

Before installing VideoLingo, ensure you have **25GB** of free disk space. Install the following dependencies based on whether you're using a local whisper model:

| Dependency | whisperX 🖥️ | whisperX ☁️ |
|:-----------|:------------|:------------|
| Anaconda 🐍 | [Download](https://www.anaconda.com/products/distribution#download-section) | [Download](https://www.anaconda.com/products/distribution#download-section) |
| Git 🌿 | [Download](https://git-scm.com/download/win) | [Download](https://git-scm.com/download/win) |
| CUDA Toolkit 12.6 🚀 | [Download](https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe) | - |
| cuDNN 9.3.0 🧠 | [Download](https://developer.download.nvidia.com/compute/cudnn/9.3.0/local_installers/cudnn_9.3.0_windows.exe) | - |

> Important: When installing Anaconda, make sure to check `Add to system PATH`. After installing CUDA and cuDNN, you need to restart your computer 🔄

### Installation Steps

Basic Python knowledge is required. Supports Windows, Mac, and Linux. If you encounter any issues, you can ask the AI assistant at the bottom right of the official website [videolingo.io](https://videolingo.io).

1. Open Anaconda Prompt and navigate to your desktop:
   ```bash
   cd desktop
   ```

2. Clone the project and change to the project directory:
   ```bash
   git clone https://github.com/Huanshere/VideoLingo.git
   cd VideoLingo
   ```

3. Create and activate a virtual environment (must use Python 3.10.0):
   ```bash
   conda create -n videolingo python=3.10.0 -y
   conda activate videolingo
   ```

4. Install ffmpeg:
   ```bash
   conda install ffmpeg
   ```

5. Run the installation script:
   ```bash
   python install.py
   ```
   Follow the prompts to choose your desired whisper method. The script will automatically install the appropriate versions of torch and whisper.

6. Only for users who need Chinese transcription:
   
   Manually download the Belle-whisper-large-v3-zh-punct model ([Baidu link](https://pan.baidu.com/s/1NyNtkEM0EMsjdCovncsx0w?pwd=938n)), and place it in the `_model_cache` folder in the project root directory. Make sure to set the **transcription language to zh** in the webpage sidebar.

7. 🎉 Start the Streamlit application by entering the command or clicking `OneKeyStart.bat`:
   ```bash
   streamlit run st.py
   ```

8. Set up your API key in the sidebar of the pop-up webpage, and make sure to select the correct whisper method.

   ![attention](https://github.com/user-attachments/assets/9ff9d8e1-5422-466f-9e28-1803f23afdc7)

9. (Optional) For more advanced settings, you can manually modify `config.yaml`. Pay attention to the command line output during the running process.

## 🚨 Common Errors and Solutions

1. **'Empty Translation Line'**: This occurs when using a less capable LLM that omits some short phrases during translation. Solution: Please switch to Claude 3.5 Sonnet and try again.

2. **'Key Error' during translation process**: 
   - Reason 1: As above, weaker models may have issues following JSON format.
   - Reason 2: For sensitive content, the LLM may refuse to translate.
   Solution: Please check the `response` and `msg` fields in `output/gpt_log/error.json`.

3. **'Retry Failed', 'SSL', 'Connection', 'Timeout'**: These are usually network issues. Solution: For users in mainland China, please try switching to a different network node and retry.


