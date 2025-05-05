<div align="center">

<img src="/docs/logo.png" alt="VideoLingo Logo" height="140">

# 連結世界，逐格前行

<a href="https://trendshift.io/repositories/12200" target="_blank"><img src="https://trendshift.io/api/badge/repositories/12200" alt="Huanshere%2FVideoLingo | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

[**English**](/README.md)｜[**简体中文**](/translations/README.zh.md)｜[**繁體中文**](/translations/README.zh-TW.md)｜[**日本語**](/translations/README.ja.md)｜[**Español**](/translations/README.es.md)｜[**Русский**](/translations/README.ru.md)｜[**Français**](/translations/README.fr.md)

</div>

## 🌟 概述 ([立即體驗 VL！](https://videolingo.io))

VideoLingo 是一個全方位的影片翻譯、本地化和配音工具，旨在生成 Netflix 品質的字幕。它消除了機器翻譯的生硬感和多行字幕，同時提供高品質配音，實現跨越語言障礙的全球知識共享。

主要功能：
- 🎥 通過 yt-dlp 下載 YouTube 影片

- **🎙️ 使用 WhisperX 進行詞級別和低幻覺字幕識別**

- **📝 基於 NLP 和 AI 的字幕分段**

- **📚 自定義 + AI 生成術語庫確保翻譯一致性**

- **🔄 三步驟翻譯-反思-調適實現影院級品質**

- **✅ Netflix 標準，僅單行字幕**

- **🗣️ 使用 GPT-SoVITS、Azure、OpenAI 等進行配音**

- 🚀 在 Streamlit 中一鍵啟動和處理

- 🌍 Streamlit UI 多語言支持

- 📝 詳細日誌記錄和進度恢復

與類似項目的區別：**僅單行字幕、更優質的翻譯、無縫配音體驗**

## 🎥 演示

<table>
<tr>
<td width="33%">

### 雙語字幕
---
https://github.com/user-attachments/assets/a5c3d8d1-2b29-4ba9-b0d0-25896829d951

</td>
<td width="33%">

### Cosy2 聲音克隆
---
https://github.com/user-attachments/assets/e065fe4c-3694-477f-b4d6-316917df7c0a

</td>
<td width="33%">

### GPT-SoVITS 配音
---
https://github.com/user-attachments/assets/47d965b2-b4ab-4a0b-9d08-b49a7bf3508c

</td>
</tr>
</table>

### 語言支持

**輸入語言支持（更多語言即將推出）：**

🇺🇸 英語 🤩 | 🇷🇺 俄語 😊 | 🇫🇷 法語 🤩 | 🇩🇪 德語 🤩 | 🇮🇹 義大利語 🤩 | 🇪🇸 西班牙語 🤩 | 🇯🇵 日語 😐 | 🇨🇳 中文* 😊

> *中文目前使用單獨的標點增強版 whisper 模型...

**翻譯支持所有語言，配音語言則取決於所選的 TTS 方法。**

## 安裝

遇到任何問題？在[**這裡**](https://share.fastgpt.in/chat/share?shareId=066w11n3r9aq6879r4z0v9rh)與我們的免費在線 AI 助手聊天以獲取幫助。

> **注意：** Windows 用戶如使用 NVIDIA GPU，請在安裝前執行以下步驟：
> 1. 安裝 [CUDA Toolkit 12.6](https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe)
> 2. 安裝 [CUDNN 9.3.0](https://developer.download.nvidia.com/compute/cudnn/9.3.0/local_installers/cudnn_9.3.0_windows.exe)
> 3. 將 `C:\Program Files\NVIDIA\CUDNN\v9.3\bin\12.6` 添加到系統 PATH
> 4. 重啟電腦

> **注意：** 需要安裝 FFmpeg。請通過包管理器安裝：
> - Windows：```choco install ffmpeg```（通過 [Chocolatey](https://chocolatey.org/)）
> - macOS：```brew install ffmpeg```（通過 [Homebrew](https://brew.sh/)）
> - Linux：```sudo apt install ffmpeg```（Debian/Ubuntu）

1. 克隆倉庫

```bash
git clone https://github.com/Huanshere/VideoLingo.git
cd VideoLingo
```

2. 安裝依賴（需要 `python=3.10`）

```bash
conda create -n videolingo python=3.10.0 -y
conda activate videolingo
python install.py
```

3. 啟動應用

```bash
streamlit run st.py
```

### Docker
或者，您可以使用 Docker（需要 CUDA 12.4 和 NVIDIA 驅動版本 >550），參見 [Docker 文檔](/docs/pages/docs/docker.en-US.md)：

```bash
docker build -t videolingo .
docker run -d -p 8501:8501 --gpus all videolingo
```

## APIs
VideoLingo 支持 OpenAI 格式的 API 和各種 TTS 接口：
- LLM：`claude-3-5-sonnet`、`gpt-4.1`、`deepseek-v3`、`gemini-2.0-flash`、...（按性能排序，使用 gemini-2.5-flash 時請謹慎...）
- WhisperX：本地運行 whisperX 或使用 302.ai API
- TTS：`azure-tts`、`openai-tts`、`siliconflow-fishtts`、**`fish-tts`**、`GPT-SoVITS`、`edge-tts`、`*custom-tts`（您可以在 custom_tts.py 中修改自己的 TTS！）

> **注意：** VideoLingo 與 **[302.ai](https://gpt302.saaslink.net/C2oHR9)** 合作 - 一個 API 密鑰即可使用所有服務（LLM、WhisperX、TTS）。或者使用 Ollama 和 Edge-TTS 在本地免費運行，無需 API！

詳細安裝、API 配置和批處理模式說明，請參閱文檔：[English](/docs/pages/docs/start.en-US.md) | [中文](/docs/pages/docs/start.zh-CN.md)

## 當前限制

1. WhisperX 轉錄性能可能受到視頻背景噪音影響，因為它使用 wav2vac 模型進行對齊。對於有大量背景音樂的視頻，請啟用語音分離增強。此外，由於 wav2vac 無法將數字字符（如"1"）映射到其口語形式（"one"），以數字或特殊字符結尾的字幕可能會提前截斷。

2. 使用較弱的模型可能會由於對響應的嚴格 JSON 格式要求而在中間過程中出錯。如果出現此錯誤，請刪除 `output` 文件夾並使用不同的 LLM 重試，否則重複執行將讀取先前的錯誤響應導致相同錯誤。

3. 由於語言之間的語速和語調差異，以及翻譯步驟的影響，配音功能可能無法 100% 完美。但是，本項目已經對語速進行了大量工程處理，以確保最佳的配音效果。

4. **多語言視頻轉錄識別將只保留主要語言**。這是因為 whisperX 在強制對齊詞級字幕時使用單一語言的專用模型，並會刪除無法識別的語言。

5. **無法分別為多個角色配音**，因為 whisperX 的說話人區分能力尚不夠可靠。

## 📄 許可證

本項目採用 Apache 2.0 許可證。特別感謝以下開源項目的貢獻：

[whisperX](https://github.com/m-bain/whisperX)、[yt-dlp](https://github.com/yt-dlp/yt-dlp)、[json_repair](https://github.com/mangiucugna/json_repair)、[BELLE](https://github.com/LianjiaTech/BELLE)

## 📬 聯繫我

- 在 GitHub 上提交 [Issues](https://github.com/Huanshere/VideoLingo/issues) 或 [Pull Requests](https://github.com/Huanshere/VideoLingo/pulls)
- 在 Twitter 上私信我：[@Huanshere](https://twitter.com/Huanshere)
- 發送郵件至：team@videolingo.io

## ⭐ Star 歷史

[![Star History Chart](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo&Timeline)

---

<p align="center">如果您覺得 VideoLingo 有幫助，請給我一個 ⭐️！</p> 