# 🚀 Getting Started

## 📋 API Configuration
This project requires Large Language Models and TTS. Multiple options are provided for each component. **Please read the configuration guide carefully 😊**

### 1. **Get API_KEY for Large Language Models**:

| Recommended Model | Recommended Provider | base_url | Price | Effect |
|:-----|:---------|:---------|:-----|:---------|
| claude-3-5-sonnet-20240620 | [Yunwu API](https://yunwu.zeabur.app/register?aff=TXMB) | https://yunwu.zeabur.app | ¥15 / 1M tokens (1/10 of official price) | 🤩 |

⚠️ Warning: The prompts involve multi-step reasoning chains and complex JSON formats. Models other than Claude 3.5 Sonnet are prone to errors. A 1-hour video costs about ¥10.

> Note: Yunwu API also supports OpenAI's tts-1 interface, which can be used in the dubbing step.

<details>
<summary>How to get API key from Yunwu API?</summary>

1. Go to [Yunwu API website](https://yunwu.zeabur.app/register?aff=TXMB)
2. Register an account and top up
3. Create a new key on the API key page
4. Make sure to check `Unlimited quota`, recommended channel is `Pure AZ 1.5x`
</details>

<details>
<summary>Can I use other models?</summary>

- ✅ Supports OAI-Like API interfaces, you can change in the Streamlit sidebar.
- ⚠️ However, other models (especially smaller ones) have weaker instruction following capabilities and are very likely to error during translation. Strongly not recommended. If errors occur, please switch models.
</details>

### 2. **TTS API**
VideoLingo provides multiple TTS integration methods. Here's a comparison (skip if only using translation without dubbing)

| TTS Solution | Pros | Cons | Chinese Effect | Non-Chinese Effect |
|:---------|:-----|:-----|:---------|:-----------|
| 🎙️ OpenAI TTS | Realistic emotions | Chinese sounds foreign | 😕 | 🤩 |
| 🔊 Azure TTS (Recommended) | Natural effect | Difficult to top up | 🤩 | 😃 |
| 🎤 Fish TTS | Authentic native speaker | Limited official models | 😂 | 😂 |
| 🗣️ GPT-SoVITS (Testing) | Best voice cloning | Currently only supports Chinese/English, requires NVIDIA GPU for inference, configuration requires relevant knowledge | 🏆 | 🚫 |

- For OpenAI TTS, recommended to use [Yunwu API](https://yunwu.zeabur.app/register?aff=TXMB), make sure to select `tts-1` for the model;
- For Azure TTS, register and top up on the [official website](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/get-started-text-to-speech?tabs=windows%2Cterminal&pivots=programming-language-python) (has free quota);
- For Fish TTS, register on the [official website](https://fish.audio/en/go-api/) (comes with $10 credit)

<details>
<summary>How to choose OpenAI voices?</summary>

Voice list can be found on the [official website](https://platform.openai.com/docs/guides/text-to-speech/voice-options), such as `alloy`, `echo`, `nova`, etc. Modify `openai_tts.voice` in `config.yaml`.

</details>
<details>
<summary>How to choose Azure voices?</summary>

Recommended to try voices in the [online demo](https://speech.microsoft.com/portal/voicegallery). You can find the voice code in the code on the right, e.g. `zh-CN-XiaoxiaoMultilingualNeural`

</details>

<details>
<summary>How to choose Fish TTS voices?</summary>

Go to the [official website](https://fish.audio/en/) to listen and choose voices. Find the voice code in the URL, e.g. Dingzhen is `54a5170264694bfc8e9ad98df7bd89c3`. Popular voices are already added in `config.yaml`. To use other voices, modify the `fish_tts.character_id_dict` dictionary in `config.yaml`.

</details>

<details>
<summary>GPT-SoVITS-v2 Tutorial</summary>

1. Check requirements and download the package from [official Yuque docs](https://www.yuque.com/baicaigongchang1145haoyuangong/ib3g1e/dkxgpiy9zb96hob4#KTvnO).

2. Place `GPT-SoVITS-v2-xxx` and `VideoLingo` in the same directory. **Note they should be parallel folders.**

3. Choose one of the following ways to configure the model:

   a. Self-trained model:
   - After training, `tts_infer.yaml` under `GPT-SoVITS-v2-xxx\GPT_SoVITS\configs` will have your model path auto-filled. Copy and rename it to `your_preferred_english_character_name.yaml`
   - In the same directory as the `yaml` file, place reference audio named `your_preferred_english_character_name_reference_audio_text.wav` or `.mp3`, e.g. `Huanyuv2_Hello, this is a test audio.wav`
   - In VideoLingo's sidebar, set `GPT-SoVITS Character` to `your_preferred_english_character_name`.

   b. Use pre-trained model:
   - Download my model from [here](https://vip.123pan.cn/1817874751/8137723), extract and overwrite to `GPT-SoVITS-v2-xxx`.
   - Set `GPT-SoVITS Character` to `Huanyuv2`.

   c. Use other trained models:
   - Place `xxx.ckpt` in `GPT_weights_v2` folder and `xxx.pth` in `SoVITS_weights_v2` folder.
   - Following method a, rename `tts_infer.yaml` and modify `t2s_weights_path` and `vits_weights_path` under `custom` to point to your models, e.g.:
  
      ```yaml
      # Example config for method b:
      t2s_weights_path: GPT_weights_v2/Huanyu_v2-e10.ckpt
      version: v2
      vits_weights_path: SoVITS_weights_v2/Huanyu_v2_e10_s150.pth
      ```
   - Following method a, place reference audio in the same directory as the `yaml` file, named `your_preferred_english_character_name_reference_audio_text.wav` or `.mp3`, e.g. `Huanyuv2_Hello, this is a test audio.wav`. The program will auto-detect and use it.
   - ⚠️ Warning: **Please use English for `character_name`** to avoid errors. `reference_audio_text` can be in Chinese. Currently in beta, may produce errors.


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
       │       └── your_preferred_english_character_name_reference_audio_text.wav
       ├── GPT_weights_v2
       │   └── [your GPT model file]
       └── SoVITS_weights_v2
           └── [your SoVITS model file]
   ```
        
After configuration, select `Reference Audio Mode` in the sidebar (see Yuque docs for details). During dubbing, VideoLingo will automatically open GPT-SoVITS inference API port in the command line, which can be closed manually after completion. Note that stability depends on the base model chosen.</details>

## 🛠️ Quick Start

VideoLingo supports Windows, macOS and Linux systems, and can run on CPU or GPU. For GPU acceleration on Windows, install these dependencies:

- [CUDA Toolkit 12.6](https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe)
- [CUDNN 9.3.0](https://developer.download.nvidia.com/compute/cudnn/9.3.0/local_installers/cudnn_9.3.0_windows.exe)

> Note: After installing CUDA and CUDNN, check if they're added to system path and restart computer 🔄

### Source Installation

Before installing VideoLingo, ensure:
1. **25GB** free disk space
2. [Anaconda](https://www.anaconda.com/download) installed (for Python environment management)
3. [Git](https://git-scm.com/downloads) installed (for cloning project code, or download manually)

Basic Python knowledge required. For any issues, ask the AI assistant at [videolingo.io](https://videolingo.io) bottom right~

1. Open Anaconda Prompt and navigate to installation directory, e.g. desktop:
   ```bash
   cd desktop
   ```

2. Clone project and enter directory:
   ```bash
   git clone https://github.com/Huanshere/VideoLingo.git
   cd VideoLingo
   ```

3. Create and activate virtual environment (**must be 3.10.0**):
   ```bash
   conda create -n videolingo python=3.10.0 -y
   conda activate videolingo
   ```

4. Run installation script:
   ```bash
   python install.py
   ```
   Script will automatically install appropriate torch version

5. 🎉 Enter command or click `OneKeyStart.bat` to launch Streamlit app:
   ```bash
   streamlit run st.py
   ```

6. Set key in sidebar of popup webpage, and note whisper method and transcription language selection

   ![en_set](https://github.com/user-attachments/assets/2f32f49b-0b7a-4ff4-930f-4e5f9bac9002)

7. Whisper transcription will automatically download models, but for users who cannot access Huggingface through command line, you can manually download whisper models and place them in the root directory: [Baidu Drive](https://pan.baidu.com/s/1Igo_FvFV4Xcb8tSYT0ktpA?pwd=e1c7)

8. More settings can be manually modified in `config.yaml`, watch command line output during operation

## 🚨 Common Errors

1. **'Empty Translation Line'**: This occurs when using a less capable LLM that omits short phrases during translation. Solution: Please retry with Claude 3.5 Sonnet.

2. **'Key Error' during translation**: 
   - Reason 1: Same as above, weaker models have poor JSON format compliance.
   - Reason 2: LLM may refuse to translate sensitive content.
   Solution: Check `response` and `msg` fields in `output/gpt_log/error.json`.

3. **'Retry Failed', 'SSL', 'Connection', 'Timeout'**: Usually network issues. Solution: Users in mainland China please switch network nodes and retry.
