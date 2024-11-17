# 🚀 Getting Started

## 📋 API Configuration
This project requires Large Language Models and TTS. **Recommended to use [SiliconFlow](https://cloud.siliconflow.cn/i/ttKDEsxE)**, which offers free credits upon registration and only needs one key for all features.

### 1. **Get API_KEY for Large Language Models**:

| Recommended Model | Recommended Provider | base_url | Price | Effect |
|:-----|:---------|:---------|:-----|:---------|
| Qwen/Qwen2.5-72B-Instruct | [SiliconFlow](https://cloud.siliconflow.cn/i/ttKDEsxE) | https://api.siliconflow.cn | ¥4 / 1M tokens | 😃 |
| claude-3-5-sonnet | [Deepbricks](https://deepbricks.ai/) | https://api.deepbricks.ai | $10 / 1M tokens | 🤩 |
| gemini-1.5-pro-latest | [Yunwu API](https://yunwu.zeabur.app/register?aff=TXMB) | https://yunwu.zeabur.app | ¥10 / 1M tokens | 😄 |

Note: Supports OpenAI interface, you can try different models. However, the process involves multi-step reasoning chains and complex JSON formats, **not recommended to use models smaller than 30B**.

### 2. **TTS API**
VideoLingo provides multiple TTS integration methods. Here's a comparison (skip if only using translation without dubbing)

| TTS Solution | Pros | Cons | Chinese Effect | Non-Chinese Effect |
|:---------|:-----|:-----|:---------|:-----------|
| 🎙️ SiliconFlow FishTTS (Recommended) | Supports cloning, simple setup | Unstable cloning effect | 😃 | 😃 |
| 🎙️ OpenAI TTS | Realistic emotions | Chinese sounds foreign | 😕 | 🤩 |
| 🔊 Azure TTS | Natural effect | Limited emotions | 🤩 | 😃 |
| 🎤 Fish TTS | Authentic native | Limited official models | 😂 | 😂 |
| 🗣️ GPT-SoVITS | Best voice cloning | Only supports Chinese/English, requires local inference, complex setup | 🏆 | 🚫 |

- For SiliconFlow FishTTS, get key from [SiliconFlow](https://cloud.siliconflow.cn/i/ttKDEsxE), note that cloning feature requires paid credits;
- For OpenAI TTS, recommended to use [Yunwu API](https://yunwu.zeabur.app/register?aff=TXMB);
- For Azure TTS, register on official website or purchase from third parties;
- For Fish TTS, register on [official website](https://fish.audio/en/go-api/) (comes with $10 credit)

<details>
<summary>SiliconFlow FishTTS Tutorial</summary>

Currently supports 3 modes:

1. `preset`: Uses fixed voice, can preview on [Official Playground](https://cloud.siliconflow.cn/playground/text-to-speech/17885302608), default is `anna`.
2. `clone(stable)`: Corresponds to fishtts api's `custom`, uses voice from uploaded audio, automatically samples first 10 seconds of video for voice, better voice consistency.
3. `clone(dynamic)`: Corresponds to fishtts api's `dynamic`, uses each sentence as reference audio during TTS, may have inconsistent voice but better effect.

</details>

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

VideoLingo supports Windows, macOS and Linux systems, and can run on CPU or GPU.

For GPU acceleration on Windows, install these dependencies:

- [CUDA Toolkit 12.6](https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe)
- [CUDNN 9.3.0](https://developer.download.nvidia.com/compute/cudnn/9.3.0/local_installers/cudnn_9.3.0_windows.exe)

> Note: After installing, add `C:\Program Files\NVIDIA\CUDNN\v9.3\bin\12.6` to system path and restart computer 🔄

### Windows One-Click Install

Make sure [Git](https://git-scm.com/downloads) is installed,

1. Download source code locally

2. Double click `OneKeyInstall&Start.bat` to complete installation and launch webpage

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

5. 🎉 Enter command to launch Streamlit app:
   ```bash
   streamlit run st.py
   ```

6. Set key in sidebar of popup webpage and start using~

   ![tutorial](https://github.com/user-attachments/assets/983ba58b-5ae3-4132-90f5-6d48801465dd)

7. Transcription step will automatically download models from huggingface, or you can download manually and place `_model_cache` folder in VideoLingo directory: [Baidu Drive](https://pan.baidu.com/s/1Igo_FvFV4Xcb8tSYT0ktpA?pwd=e1c7)

8. (Optional) More settings can be manually modified in `config.yaml`, watch command line output during operation

## 🚨 Common Errors

1. **'Key Error' during translation**: 
   - Reason 1: Same as above, weaker models have poor JSON format compliance.
   - Reason 2: LLM may refuse to translate sensitive content.
   Solution: Check `response` and `msg` fields in `output/gpt_log/error.json`.

2. **'Retry Failed', 'SSL', 'Connection', 'Timeout'**: Usually network issues. Solution: Users in mainland China please switch network nodes and retry.
