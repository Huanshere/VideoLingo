# VideoLingo: Connecting the World, Frame by Frame

## 🌟 Overview ([Try VideoLingo Now!](https://videolingo.io))

VideoLingo is an all-in-one video translation, localization, and dubbing tool aimed at generating Netflix-quality subtitles. It eliminates stiff machine translations and multi-line subtitles while adding high-quality dubbing, enabling global knowledge sharing across language barriers.

Key features:
- 🎥 YouTube video download via yt-dlp

- **🎙️ Word-level subtitle recognition with Qwen3-ASR + ForcedAligner (WhisperX optional)**

- **📝 NLP and GPT-based subtitle segmentation**

- **📚 GPT-generated terminology for coherent translation**

- **🔄 3-step direct translation, reflection, and adaptation for professional-level quality**

- **✅ Netflix-standard single-line subtitles only**

- **🗣️ Dubbing alignment with GPT-SoVITS and other methods**

- 🚀 One-click startup and output in Streamlit

- 📝 Detailed logging with progress resumption

Difference from similar projects: **Single-line subtitles only, superior translation quality, seamless dubbing experience**

## 🎥 Demo

<table>
<tr>
<td width="50%">

### Russian Translation
---
https://github.com/user-attachments/assets/25264b5b-6931-4d39-948c-5a1e4ce42fa7

</td>
<td width="50%">

### GPT-SoVITS Dubbing
---
https://github.com/user-attachments/assets/47d965b2-b4ab-4a0b-9d08-b49a7bf3508c

</td>
</tr>
</table>

### Language Support

**Input Language Support(more to come):**

🇺🇸 English 🤩 | 🇷🇺 Russian 😊 | 🇫🇷 French 🤩 | 🇩🇪 German 🤩 | 🇮🇹 Italian 🤩 | 🇪🇸 Spanish 🤩 | 🇯🇵 Japanese 😐 | 🇨🇳 Chinese* 😊

> *Local recognition uses Qwen3-ASR (1.7B by default, 0.6B selectable). The optional WhisperX fallback uses a punctuation-enhanced Belle Whisper model for Chinese.

**Translation supports all languages, while dubbing language depends on the chosen TTS method.**

## Installation

Install [Git](https://git-scm.com/downloads), [uv](https://docs.astral.sh/uv/getting-started/installation/) and [FFmpeg](https://ffmpeg.org/download.html) first. Reopen your terminal and verify they are on PATH. For NVIDIA runtime requirements, follow the [installation guide](start.en-US.md#gpu-runtime). WhisperX is optional and not installed by default; see [WhisperX (optional)](whisperx-optional.en-US.md).

1. Clone the repository

```bash
git clone https://github.com/Huanshere/VideoLingo.git
cd VideoLingo
```

2. Create the Python 3.13 environment and install dependencies

```bash
uv run --no-project --python 3.13 setup_env.py
```

3. Start the application

```bash
.venv\Scripts\python -m streamlit run st.py  # Windows
.venv/bin/python -m streamlit run st.py     # macOS / Linux
```

### Docker
For Linux NVIDIA containers, use Docker with a compatible driver and NVIDIA Container Toolkit. The image uses the same Python 3.13 setup; see [Docker docs](/docs/pages/docs/docker.en-US.md):

```bash
docker build -t videolingo .
docker run -d -p 8501:8501 --gpus all videolingo
```

## API
The project supports OpenAI-Like API format and various dubbing interfaces:
- Choose an OpenAI-compatible Chat Completions provider and a model capable of returning structured JSON. Set the API URL, key and model in the sidebar.
- `azure-tts`, `openai-tts`, `siliconflow-fishtts`, `fish-tts`, `GPT-SoVITS`

For detailed installation, API configuration, and batch mode instructions, please refer to the documentation: [English](/docs/pages/docs/start.en-US.md) | [中文](/docs/pages/docs/start.zh-CN.md)

## Current Limitations

1. Transcription and word timestamps may be affected by background noise. For videos with loud background music, enable Voice Separation Enhancement: Qwen3-ASR still transcribes the original audio, while the ForcedAligner aligns against the separated vocals. Punctuation is re-attached to aligned words heuristically; in rare cases a word may lose its punctuation.

2. Using weaker models can lead to errors during intermediate processes due to strict JSON format requirements for responses. If this error occurs, please delete the `output` folder and retry with a different LLM, otherwise repeated execution will read the previous erroneous response causing the same error.

3. The dubbing feature may not be 100% perfect due to differences in speech rates and intonation between languages, as well as the impact of the translation step. However, this project has implemented extensive engineering processing for speech rates to ensure the best possible dubbing results.

4. **Multilingual video transcription recognition is only reliable for the main language**. Alignment runs with one language per audio window, so text and timing in other languages are not guaranteed.

5. **Cannot dub multiple characters separately**; recognition does not distinguish speakers.

## 📄 License

This project is licensed under the Apache 2.0 License. Special thanks to the following open source projects for their contributions:

[Qwen3-ASR](https://github.com/Qwen/Qwen3-ASR), [MLX Audio](https://github.com/Blaizzy/mlx-audio), [whisperX](https://github.com/m-bain/whisperX), [yt-dlp](https://github.com/yt-dlp/yt-dlp), [json_repair](https://github.com/mangiucugna/json_repair), [BELLE](https://github.com/LianjiaTech/BELLE)

## 📬 Contact Us

- Join our Discord: https://discord.gg/9F2G92CWPp
- Submit [Issues](https://github.com/Huanshere/VideoLingo/issues) or [Pull Requests](https://github.com/Huanshere/VideoLingo/pulls) on GitHub
- Follow me on Twitter: [@Huanshere](https://twitter.com/Huanshere)
- Email me at: team@videolingo.io

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo&Timeline)

---

<p align="center">If you find VideoLingo helpful, please give us a ⭐️!</p>
