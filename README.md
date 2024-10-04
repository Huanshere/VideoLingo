<div align="center">

<img src="docs/logo.png" alt="VideoLingo Logo" height="140">

# VideoLingo: Connecting the World, Frame by Frame
<p align="center">
  <a href="https://www.python.org" target="_blank"><img src="https://img.shields.io/badge/Python-3.10-blue.svg" alt="Python"></a>
  <a href="https://github.com/Huanshere/VideoLingo/blob/main/LICENSE" target="_blank"><img src="https://img.shields.io/github/license/Huanshere/VideoLingo.svg" alt="License"></a>
  <a href="https://github.com/Huanshere/VideoLingo/stargazers" target="_blank"><img src="https://img.shields.io/github/stars/Huanshere/VideoLingo.svg" alt="GitHub stars"></a>
  <a href="https://colab.research.google.com/github/Huanshere/VideoLingo/blob/main/VideoLingo_colab.ipynb" target="_blank"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a>
</p>

[**English**](README.md)｜[**中文**](README.zh.md) | [**日本語**](README.ja.md)


</div>

## 🌟 Project Introduction

VideoLingo is an all-in-one video translation and localization tool that generates Netflix-quality subtitles, eliminates awkward translations and multi-line captions, and provides high-quality dubbing. With a simple Streamlit interface, users can effortlessly transform video links into localized content with bilingual subtitles and professional dubbing in just a few clicks..

Key features and functionalities:
- 🎥 Uses yt-dlp to download videos from YouTube links

- 🎙️ Uses WhisperX for word-level timeline subtitle recognition

- **📝 Uses NLP and GPT for subtitle segmentation based on sentence meaning**

- **📚 GPT summarizes and extracts terminology knowledge base for context-aware translation**

- **🔄 Three-step direct translation, reflection, and paraphrasing, rivaling professional subtitle translation quality**

- **✅ Checks single-line length according to Netflix standards, absolutely no double-line subtitles**

- **🗣️ Uses methods like GPT-SoVITS for high-quality aligned dubbing**

- 🚀 One-click integrated package launch, one-click video production in Streamlit

- 📝 Detailed logging of each operation step, supporting interruption and progress resumption at any time

- 🌐 Comprehensive multi-language support, easily achieving cross-language video localization

## 🎥 Demo

<table>
<tr>
<td width="25%">

### Russian Translation
---
https://github.com/user-attachments/assets/25264b5b-6931-4d39-948c-5a1e4ce42fa7

</td>
<td width="25%">

### GPT-SoVITS
---
https://github.com/user-attachments/assets/47d965b2-b4ab-4a0b-9d08-b49a7bf3508c

</td>
<td width="25%">

### Fish TTS Ding Zhen
---
https://github.com/user-attachments/assets/e7bb9090-d2ef-4261-9dc5-56bd67dc710d

</td>
<td width="25%">

### OAITTS
---
https://github.com/user-attachments/assets/85c64f8c-06cf-4af9-b153-ee9d2897b768

</td>
</tr>
</table>

### Language Support:

Currently supported input languages and examples:

| Input Language | Support Level | Translation Demo | Dubbing Demo |
|----------------|---------------|-------------------|--------------|
| English | 🤩 | [English to Chinese](https://github.com/user-attachments/assets/127373bb-c152-4b7a-8d9d-e586b2c62b4b) | TODO |
| Russian | 😊 | [Russian to Chinese](https://github.com/user-attachments/assets/25264b5b-6931-4d39-948c-5a1e4ce42fa7) | TODO |
| French | 🤩 | [French to Japanese](https://github.com/user-attachments/assets/3ce068c7-9854-4c72-ae77-f2484c7c6630) | TODO |
| German | 🤩 | [German to Chinese](https://github.com/user-attachments/assets/07cb9d21-069e-4725-871d-c4d9701287a3) | TODO |
| Italian | 🤩 | [Italian to Chinese](https://github.com/user-attachments/assets/f1f893eb-dad3-4460-aaf6-10cac999195e) | TODO |
| Spanish | 🤩 | [Spanish to Chinese](https://github.com/user-attachments/assets/c1d28f1c-83d2-4f13-a1a1-859bd6cc3553) | TODO |
| Japanese | 😐 | [Japanese to Chinese](https://github.com/user-attachments/assets/856c3398-2da3-4e25-9c36-27ca2d1f68c2) | TODO |
| Chinese* | 🤩 | [Chinese to English](https://github.com/user-attachments/assets/48f746fe-96ff-47fd-bd23-59e9202b495c) | [Professor Luo Xiang's Talk Show](https://github.com/user-attachments/assets/85c64f8c-06cf-4af9-b153-ee9d2897b768) |
> *Chinese requires separate configuration of the whisperX model, see source code installation

Translation languages support all languages that the large language model can handle, while dubbing languages depend on the chosen TTS method.

## 🚀 One-Click Integrated Package for Windows

### Important Notes:

1. The integrated package uses the CPU version of torch, with a size of about **2.6G**.
2. When using UVR5 for voice separation in the dubbing step, the CPU version will be significantly slower than GPU-accelerated torch.
3. The integrated package **only supports calling whisperXapi ☁️ via API**, and does not support running whisperX locally 💻.
4. The whisperXapi used in the integrated package does not support Chinese transcription. If you need to use Chinese, please install from source code and use locally run whisperX 💻.
5. The integrated package has not yet performed UVR5 voice separation in the transcription step, so it is not recommended to use videos with noisy BGM.

If you need the following features, please install from source code (requires an Nvidia GPU and at least **20G** of disk space):
- Input language is Chinese
- Run whisperX locally 💻
- Use GPU-accelerated UVR5 for voice separation
- Transcribe videos with noisy BGM

### Download and Usage Instructions

1. Download the `v1.4` one-click package (800M): [Download Directly](https://vip.123pan.cn/1817874751/8209290) | [Baidu Backup](https://pan.baidu.com/s/1H_3PthZ3R3NsjS0vrymimg?pwd=ra64)

2. After extracting, double-click `OneKeyStart.bat` in the folder

3. In the opened browser window, configure the necessary settings in the sidebar, then create your video with one click!
  ![attentionen](https://github.com/user-attachments/assets/9ff9d8e1-5422-466f-9e28-1803f23afdc7)


> 💡 Note: This project requires configuration of large language models, WhisperX, and TTS. Please carefully read the **API Preparation** section below

## 📋 API Preparation
This project requires the use of large language models, WhisperX, and TTS. Multiple options are provided for each component. **Please read the configuration guide carefully 😊**
### 1. **Obtain API_KEY for Large Language Models**:

| Recommended Model | Recommended Provider | base_url | Price | Effect |
|:-----|:---------|:---------|:-----|:---------|
| claude-3-5-sonnet-20240620 (default) | [Yunwu API](https://yunwu.zeabur.app/register?aff=TXMB) | https://yunwu.zeabur.app | ¥15 / 1M tokens | 🤩 |
| deepseek-coder | [deepseek](https://platform.deepseek.com/api_keys) | https://api.deepseek.com | ¥2 / 1M tokens | 😲 |
> Note: Yunwu API also supports OpenAI's tts-1 interface, which can be used in the dubbing step.

> Reminder: deepseek has a very low probability of errors during translation. If errors occur, please switch to the claude 3.5 sonnet model.

#### Common Questions

<details>
<summary>Which model should I choose?</summary>

- 🌟 Default use of Claude 3.5, excellent translation quality, very good coherence, no AI flavor.
- 🚀 If using deepseek, translating a 1-hour video costs about ¥1, with average results.
</details>

<details>
<summary>How to get an API key?</summary>

1. Click the link above to visit the recommended provider
2. Register and recharge your account.  
3. Create a new API key on the API key page
4. For Yunwu API, make sure to check `Unlimited Quota`, select the `claude-3-5-sonnet-20240620` model, and it is recommended to choose the `Pure AZ 1.5x` channel.
</details>

<details>
<summary>Can I use other models?</summary>

- ✅ Supports OAI-Like API interfaces, but you need to change it yourself in the Streamlit sidebar.
- ⚠️ However, other models (especially small models) have weak ability to follow instructions and are very likely to report errors during translation, which is strongly discouraged.
</details>

### 2. **Prepare Replicate Token** (Only when using whisperXapi ☁️)

VideoLingo uses WhisperX for speech recognition, supporting both local deployment and cloud API.
#### Comparison of options:
| Option | Disadvantages |
|:-----|:-----|
| **whisperX 🖥️** | • Install CUDA 🛠️<br>• Download model 📥<br>• High VRAM requirement 💾 |
| **whisperXapi ☁️** | • Requires VPN 🕵️‍♂️<br>• Visa card 💳<br>• **Poor Chinese effect** 🚫 |

#### Obtaining the token
   - Register at [Replicate](https://replicate.com/account/api-tokens), bind a Visa card payment method, and obtain the token
   - **Or join the QQ group to get a free test token from the group announcement**

### 3. **TTS API**
VideoLingo provides multiple TTS integration methods. Here's a comparison (skip this if you're only translating without dubbing):

| TTS Option | Advantages | Disadvantages | Chinese Effect | Non-Chinese Effect |
|:---------|:-----|:-----|:---------|:-----------|
| 🎙️ OpenAI TTS | Realistic emotion | Chinese sounds like a foreigner | 😕 | 🤩 |
| 🔊 Azure TTS  | Natural effect | Inconvenient recharge | 🤩 | 😃 |
| 🎤 Fish TTS (Recommended) | Excellent | Requires recharge | 😱 | 😱 |
| 🗣️ GPT-SoVITS (beta) | Local voice cloning | Currently only supports English input Chinese output, requires GPU for model inference, best for single-person videos without obvious BGM, and the base model should be close to the original voice | 😂 | 🚫 |

- For OpenAI TTS, we recommend using [Yunwu API](https://yunwu.zeabur.app/register?aff=TXMB);
- **Azure TTS free keys can be obtained in the QQ group announcement** or you can register and recharge yourself on the [official website](https://learn.microsoft.com/zh-cn/azure/ai-services/speech-service/get-started-text-to-speech?tabs=windows%2Cterminal&pivots=programming-language-python);
- **Fish TTS free keys can be obtained in the QQ group announcement** or you can register and recharge yourself on the [official website](https://fish.audio/zh-CN/go-api/)

<details>
<summary>How to choose an OpenAI voice?</summary>

You can find the voice list on the [official website](https://platform.openai.com/docs/guides/text-to-speech/voice-options), such as `alloy`, `echo`, `nova`, and `fable`. Modify `OAI_VOICE` in `config.py` to change the voice.

</details>

<details>
<summary>How to choose an Azure voice?</summary>

It is recommended to listen and choose the voice you want in the [online experience](https://speech.microsoft.com/portal/voicegallery), and find the corresponding code for that voice in the right-hand code, such as `zh-CN-XiaoxiaoMultilingualNeural`.

</details>

<details>
<summary>How to choose a Fish TTS voice?</summary>

Go to the [official website](https://fish.audio/zh-CN/) to listen and choose the voice you want, and find the corresponding code for that voice in the URL, such as Ding Zhen is `54a5170264694bfc8e9ad98df7bd89c3`. Popular voices have been added to `config.py`, just modify `FISH_TTS_CHARACTER`. If you need to use other voices, please modify the `FISH_TTS_CHARACTER_ID_DICT` dictionary in `config.py`.

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
        
After configuration, make sure to select `Reference Audio Mode` in the webpage sidebar. VideoLingo will automatically open the inference API port of GPT-SoVITS in the pop-up command line during the dubbing step. You can manually close it after dubbing is complete. Note that this method is still not very stable and may result in missing words or sentences or other bugs, so please use it with caution.</details>

## 🛠️ Source Code Installation Process

### Windows Prerequisites

Before starting the installation of VideoLingo, please ensure you have **20G** of free disk space and complete the following steps:

| Dependency | whisperX 🖥️ | whisperX ☁️ |
|:-----|:-------------------|:----------------|
| Anaconda 🐍 | [Download](https://www.anaconda.com/products/distribution#download-section) | [Download](https://www.anaconda.com/products/distribution#download-section) |
| Git 🌿 | [Download](https://git-scm.com/download/win) | [Download](https://git-scm.com/download/win) |
| Cuda Toolkit 12.6 🚀 | [Download](https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe) | - |
| Cudnn 9.3.0 🧠 | [Download](https://developer.download.nvidia.com/compute/cudnn/9.3.0/local_installers/cudnn_9.3.0_windows.exe) | - |

> Note: When installing Anaconda, check "Add to system Path", and restart your computer after installation 🔄

### Installation Steps

Some Python knowledge is required. Supports Win, Mac, Linux. If you encounter any issues, you can ask GPT about the entire process~

1. Open Anaconda Prompt and switch to the desktop directory:
   ```bash
   cd desktop
   ```

2. Clone the project and switch to the project directory:
   ```bash
   git clone https://github.com/Huanshere/VideoLingo.git
   cd VideoLingo
   ```

3. Create and activate the virtual environment (**must be 3.10.0**):
   ```bash
   conda create -n videolingo python=3.10.0 -y
   conda activate videolingo
   ```

4. Run the installation script:
   ```bash
   python install.py
   ```
   Follow the prompts to select the desired Whisper method, the script will automatically install the corresponding torch and whisper versions

5. Only for users who need to use Chinese transcription:
   
   Please manually download the Belle-whisper-large-v3-zh-punct model ([Baidu link](https://pan.baidu.com/s/1NyNtkEM0EMsjdCovncsx0w?pwd=938n)), and overwrite it in the `_model_cache` folder in the project root directory

6. 🎉 Enter the command or click `OneKeyStart.bat` to launch the Streamlit application:
   ```bash
   streamlit run st.py
   ```

7. Set the key in the sidebar of the pop-up webpage, and be sure to select the whisper method

   ![attentionen](https://github.com/user-attachments/assets/9ff9d8e1-5422-466f-9e28-1803f23afdc7)

8. (Optional) More advanced settings can be manually modified in `config.py`

<!-- This project uses structured module development. You can run `core\step__.py` files in sequence. Technical documentation: [Chinese](./docs/README_guide_zh.md) | [English](./docs/README_guide_en.md) (To be updated) -->

## ⚠️ Precautions

1. UVR5 has high memory requirements. 16G RAM can process up to 30min, 32GB RAM can process up to 50min. Please be cautious with long videos.
   
2. There's a very small chance of 'phrase' errors occurring in the translation step. If encountered, please report.
   
3. The dubbing function's quality is unstable. For best quality, please try to choose TTS speed suitable for the original video. For example, OAITTS speed is relatively fast, while for FishTTS speed, please listen to samples before choosing.

## 📄 License

This project is licensed under the Apache 2.0 License. When using this project, please follow these rules:

1. When publishing works, it is **recommended (not mandatory) to credit VideoLingo for subtitle generation**.
2. Follow the terms of the large language models and TTS used for proper attribution.
3. If you copy the code, please include the full copy of the Apache 2.0 License.

We sincerely thank the following open-source projects for their contributions, which provided important support for the development of VideoLingo:

- [whisperX](https://github.com/m-bain/whisperX)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [json_repair](https://github.com/mangiucugna/json_repair)
- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)
- [BELLE](https://github.com/LianjiaTech/BELLE)

## 📬 Contact Us

- Join our QQ Group: 875297969
- Submit [Issues](https://github.com/Huanshere/VideoLingo/issues) or [Pull Requests](https://github.com/Huanshere/VideoLingo/pulls) on GitHub
- Follow me on Twitter: [@Huanshere](https://twitter.com/Huanshere)
- Visit the official website: [videolingo.io](https://videolingo.io)

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo&Timeline)

---

<p align="center">If you find VideoLingo helpful, please give us a ⭐️!</p>
