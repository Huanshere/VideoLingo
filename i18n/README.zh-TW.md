<div align="center">

<img src="/docs/logo.png" alt="VideoLingo Logo" height="140">

# 連接世界每一幀

[Website](https://videolingo.io) | [Documentation](https://docs.videolingo.io/docs/start)

[**English**](/README.md)｜[**中文**](/i18n/README.zh.md)

**QQ群：875297969**

</div>

## 🌟 簡介（[免費在線體驗！](https://videolingo.io)）

VideoLingo 是一站式影片翻譯在地化配音工具，能夠一鍵生成 Netflix 級別的高品質字幕，告別生硬機翻，告別多行字幕，還能加上高品質的克隆配音，讓全世界的知識能夠跨越語言的障礙共享。

主要特點和功能：
- 🎥 使用 yt-dlp 從 Youtube 連結下載影片

- **🎙️ 使用 WhisperX 進行單詞級和低幻覺字幕識別**

- **📝 使用 NLP 和 AI 進行字幕分割**

- **📚 自訂 + AI 生成術語庫，保證翻譯連貫性**

- **🔄 三步直譯、反思、意譯，實現影視級翻譯品質**

- **✅ 按照 Netflix 標準檢查單行長度，絕無雙行字幕**

- **🗣️ 支援 GPT-SoVITS、Azure、OpenAI 等多種配音方案**

- 🚀 整合包一鍵啟動，在 streamlit 中一鍵出片

- 📝 詳細記錄每步操作日誌，支援隨時中斷和恢復進度

與同類專案相比的優勢：**絕無多行字幕，最佳的翻譯品質，無縫的配音體驗**

## 🎥 效果展示

<table>
<tr>
<td width="50%">

### 俄語翻譯
---
https://github.com/user-attachments/assets/25264b5b-6931-4d39-948c-5a1e4ce42fa7

</td>
<td width="50%">

### GPT-SoVITS配音
---
https://github.com/user-attachments/assets/47d965b2-b4ab-4a0b-9d08-b49a7bf3508c

</td>
</tr>
</table>

### 語言支援

**輸入語言支援：**

🇺🇸 英語 🤩  |  🇷🇺 俄語 😊  |  🇫🇷 法語 🤩  |  🇩🇪 德語 🤩  |  🇮🇹 義大利語 🤩  |  🇪🇸 西班牙語 🤩  |  🇯🇵 日語 😐  |  🇨🇳 中文* 😊

> *中文使用單獨的標點增強後的 whisper 模型

**翻譯語言支援所有語言，配音語言取決於選取的TTS。**

## 安裝

> **注意:** 在 Windows 上使用 NVIDIA GPU 加速需要先完成以下步驟:
> 1. 安裝 [CUDA Toolkit 12.6](https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe)
> 2. 安裝 [CUDNN 9.3.0](https://developer.download.nvidia.com/compute/cudnn/9.3.0/local_installers/cudnn_9.3.0_windows.exe)
> 3. 將 `C:\Program Files\NVIDIA\CUDNN\v9.3\bin\12.6` 添加到系統環境變數 PATH 中
> 4. 重啟電腦

> **注意:** FFmpeg 是必需的，請通過包管理器安裝：
> - Windows：```choco install ffmpeg```（通過 [Chocolatey](https://chocolatey.org/)）
> - macOS：```brew install ffmpeg```（通過 [Homebrew](https://brew.sh/)）
> - Linux：```sudo apt install ffmpeg```（Debian/Ubuntu）或 ```sudo dnf install ffmpeg```（Fedora）

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
還可以選擇使用 Docker（要求 CUDA 12.4 和 NVIDIA Driver 版本 >550），詳見[Docker文檔](/docs/pages/docs/docker.zh-CN.md)：

```bash
docker build -t videolingo .
docker run -d -p 8501:8501 --gpus all videolingo
```

## API
本專案支援 OpenAI-Like 格式的 api 和多種配音接口：
- `claude-3-5-sonnet-20240620`, **`gemini-2.0-flash-exp`**, `gpt-4o`, `deepseek-coder`, ...（按效果排序）
- `azure-tts`, `openai-tts`, `siliconflow-fishtts`, **`fish-tts`**, `GPT-SoVITS`, `edge-tts`, `*custom-tts`(ask gpt to help you define in custom_tts.py)

> **注意：** VideoLingo 現已與 [302.ai](https://gpt302.saaslink.net/C2oHR9) 集成，**一個 API KEY** 即可同時支援 LLM 和 TTS！同時也支援完全本地部署，使用 Ollama 作為 LLM 和 Edge-TTS 作為配音，無需雲端 API！

詳細的安裝、API 配置、漢化、批量說明可以參見文檔：[English](/docs/pages/docs/start.en-US.md) | [簡體中文](/docs/pages/docs/start.zh-CN.md)

## 當前限制
1. WhisperX 轉錄效果可能受到影片背景聲影響，因為使用了 wav2vac 模型進行對齊。對於背景音樂較大的影片，請開啟人聲分離增強。另外，如果字幕以數字或特殊符號結尾，可能會導致提前截斷，這是因為 wav2vac 無法將數字字符（如"1"）映射到其發音形式（"one"）。

2. 使用較弱模型時容易在中間過程報錯，這是因為對響應的 json 格式要求較為嚴格。如果出現此錯誤，請刪除 `output` 文件夾後更換 llm 重試，否則重複執行會讀取上次錯誤的響應導致同樣錯誤。

3. 配音功能由於不同語言的語速和語調差異，還受到翻譯步驟的影響，可能不能 100% 完美，但本專案做了非常多的語速上的工程處理，盡可能保證配音效果。

4. **多語言影片轉錄識別僅僅只會保留主要語言**，這是由於 whisperX 在強制對齊單詞級字幕時使用的是針對單個語言的特化模型，會因為不認識另一種語言而刪去。

5. **無法多角色分別配音**，whisperX 的說話人區分效果不夠好用。

## 📄 許可證

本專案採用 Apache 2.0 許可證，衷心感謝以下開源專案的貢獻：

[whisperX](https://github.com/m-bain/whisperX), [yt-dlp](https://github.com/yt-dlp/yt-dlp), [json_repair](https://github.com/mangiucugna/json_repair), [BELLE](https://github.com/LianjiaTech/BELLE)

## 📬 聯繫我們

- 加入我們的 QQ 群尋求解答：875297969
- 在 GitHub 上提交 [Issues](https://github.com/Huanshere/VideoLingo/issues) 或 [Pull Requests](https://github.com/Huanshere/VideoLingo/pulls)
- 關注我的 Twitter：[@Huanshere](https://twitter.com/Huanshere)
- 聯繫郵箱：team@videolingo.io

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo&Timeline)
