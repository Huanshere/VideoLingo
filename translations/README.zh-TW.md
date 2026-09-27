<div align="center">

<img src="/docs/logo.png" alt="VideoLingo Logo" height="140">

# 連結世界，逐格前行

<a href="https://trendshift.io/repositories/12200" target="_blank"><img src="https://trendshift.io/api/badge/repositories/12200" alt="Huanshere%2FVideoLingo | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

[**English**](/README.md)｜[**简体中文**](/translations/README.zh.md)｜[**繁體中文**](/translations/README.zh-TW.md)｜[**日本語**](/translations/README.ja.md)｜[**Español**](/translations/README.es.md)｜[**Русский**](/translations/README.ru.md)｜[**Français**](/translations/README.fr.md)

</div>

## 🌟 概述 ([立即體驗 VL！](https://videolingo.io))

VideoLingo 在 Streamlit 介面中整合語音辨識、字幕翻譯、分句和配音，可產生字幕檔案，以及可選的字幕影片或配音影片。翻譯品質取決於原始音訊、語言和所選模型。

主要功能：
- 🎥 通過 yt-dlp 下載 YouTube 影片

- 使用 Qwen3-ASR + Qwen3-ForcedAligner 進行詞級語音辨識與時間對齊

- **📝 基於 NLP 和 AI 的字幕分段**

- **📚 自定義 + AI 生成術語庫確保翻譯一致性**

- 直譯，以及可選的反思和自然改寫

- 按可設定的長度限制切分字幕

- **🗣️ 使用 GPT-SoVITS、Azure、OpenAI 等進行配音**

- 🚀 在 Streamlit 中一鍵啟動和處理

- 🌍 Streamlit UI 多語言支持

- 📝 詳細日誌記錄和進度恢復

- 🔍 模型搜尋選擇器，自動從 API 獲取完整模型清單，支援搜尋篩選

- ⏯️ 任務控制 — 處理過程中可隨時暫停、繼續或停止

在同一個專案中完成轉錄、翻譯、字幕排版和配音。

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

🇺🇸 英語 🤩 | 🇷🇺 俄語 😊 | 🇫🇷 法語 🤩 | 🇩🇪 德語 🤩 | 🇮🇹 義大利語 🤩 | 🇪🇸 西班牙語 🤩 | 🇯🇵 日語 😊 | 🇨🇳 中文 🤩

配音語言取決於所選 TTS。

## 安裝

VideoLingo 支援 Windows、Linux、macOS 14 或更新版本的 Apple Silicon Mac，以及使用 CPU 辨識的 Intel Mac。安裝統一使用 Python 3.12。

### Windows 一鍵安裝 🎉

1. 開啟[最新版本頁面](https://github.com/Huanshere/VideoLingo/releases/latest)，下載 **Source code (zip)**。
2. 解壓縮到桌面等方便找到的位置，開啟解壓縮後的資料夾。
3. 雙擊 `OneKeyStart.bat`，保持視窗開啟，等待所需元件下載與安裝完成。首次執行需要連網，可能需要一些時間。
4. VideoLingo 開啟後，在側邊欄填入 API 網址、金鑰和模型。下次仍雙擊同一個 `OneKeyStart.bat`，它會檢查安裝狀態並啟動程式。

使用這個 Windows 方法，不需要自行安裝 Git、uv 或 Python。

### 從原始碼安裝（Windows、macOS、Linux）

```bash
git clone https://github.com/Huanshere/VideoLingo.git
cd VideoLingo
uv run --no-project --python 3.12 setup_env.py --yes --launch
```

之後啟動：Windows 雙擊 `OneKeyStart.bat`；macOS/Linux 執行 `.venv/bin/python -m streamlit run st.py`。Apple Silicon 自動使用 MLX，Intel Mac 自動使用 CPU 辨識；可選的人聲分離暫不自動安裝。

#### Docker（可選）

在 Linux 上部署 NVIDIA GPU 容器，需要 Docker、相容的顯卡驅動和 [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)。映像檔使用相同的 Python 3.12 安裝流程和應用程式依賴，預設 CUDA 12.8.1/cu128。相容的 CUDA 12.6 方案及資料持久化設定見 [Docker 文件](/docs/pages/docs/docker.zh-CN.md)。

```bash
docker build -t videolingo .
docker run -d -p 8501:8501 --gpus all videolingo
```

## APIs
VideoLingo 支持 OpenAI 格式的 API 和各種 TTS 接口：
- LLM：自行選擇相容 OpenAI Chat Completions、能回傳流程所需結構化 JSON 的服務與模型。推薦 [OpenLux](https://www.openlux.ai/register?aff=wKYu) 中轉，API 網址填 `https://api.openlux.ai/v1`。預設性價比高用 GPT-6 Luna，模型 ID 填 `gpt-6-luna`；品質更好用 GPT-6 Sol，模型 ID 填 `gpt-6-sol`；品質最好用 Claude Opus 5.5，模型 ID 填 `claude-opus-5-5`。OpenLux 中轉約價見安裝文件。在側欄設定 API 網址、金鑰和模型。
- 語音辨識：本地執行 Qwen3-ASR + ForcedAligner（預設），或使用 ElevenLabs API。安裝器不會安裝 WhisperX；若要把它當作後端，見 [WhisperX（手動安裝）](../docs/pages/docs/whisperx-manual.zh-CN.md)。
- TTS：Azure、OpenAI、Fish TTS、SiliconFlow Fish/CosyVoice2、GPT-SoVITS、Edge TTS、F5-TTS，以及 `core/tts_backend/custom_tts.py` 中的自訂適配器。

詳細安裝、API 配置和批處理模式說明，請參閱文檔：[English](/docs/pages/docs/start.en-US.md) | [中文](/docs/pages/docs/start.zh-CN.md)

## 當前限制

1. 背景雜音和各語言的對齊模型會影響辨識及詞級時間戳，人聲分離可能有所幫助。數字、符號可能缺少可靠的詞級時間，需要檢查產生的字幕。

2. LLM 輸出需滿足流程要求的 JSON 結構，失敗時檢查 `output/gpt_log/error.json`。重試可能重用已成功的回應快取和已完成的輸出，僅更換模型不會重做所有步驟。不要一開始就刪除全部輸出。

3. 配音品質和時間匹配取決於翻譯、TTS 服務及語速，變速處理不能保證表達自然或完全同步。

4. 本地辨識在每個音訊片段中使用一種主要辨識和對齊語言，混合語言語音不保證每種語言的文字和時間都準確。

5. 配音流程不會自動為每個說話人分配不同的聲音。

## 📄 許可證

本項目採用 Apache 2.0 許可證。特別感謝以下開源項目的貢獻：

[Qwen3-ASR](https://github.com/Qwen/Qwen3-ASR)、[MLX Audio](https://github.com/Blaizzy/mlx-audio)、[whisperX](https://github.com/m-bain/whisperX)、[yt-dlp](https://github.com/yt-dlp/yt-dlp)、[json_repair](https://github.com/mangiucugna/json_repair)、[BELLE](https://github.com/LianjiaTech/BELLE)

## 📬 聯繫我

- 在 GitHub 上提交 [Issues](https://github.com/Huanshere/VideoLingo/issues) 或 [Pull Requests](https://github.com/Huanshere/VideoLingo/pulls)
- 在 Twitter 上私信我：[@Huanshere](https://twitter.com/Huanshere)
- 發送郵件至：team@videolingo.io

## ⭐ Star 歷史

[![Star History Chart](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo&Timeline)

---

<p align="center">如果您覺得 VideoLingo 有幫助，請給我一個 ⭐️！</p>
