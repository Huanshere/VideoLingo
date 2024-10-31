<div align="center">

<img src="/docs/logo.png" alt="VideoLingo Logo" height="140">

# 連接世界每一幀
<p align="center">
  <a href="https://www.python.org" target="_blank"><img src="https://img.shields.io/badge/Python-3.10-blue.svg" alt="Python"></a>
  <a href="https://github.com/Huanshere/VideoLingo/blob/main/LICENSE" target="_blank"><img src="https://img.shields.io/github/license/Huanshere/VideoLingo.svg" alt="License"></a>
  <a href="https://colab.research.google.com/github/Huanshere/VideoLingo/blob/main/VideoLingo_colab.ipynb" target="_blank"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a>
  <a href="https://discord.gg/9F2G92CWPp" target="_blank"><img src="https://img.shields.io/badge/Discord-Join%20Us-7289DA?style=flat-square&logo=discord&logoColor=white" alt="Discord"></a>
  <a href="https://github.com/Huanshere/VideoLingo/stargazers" target="_blank"><img src="https://img.shields.io/github/stars/Huanshere/VideoLingo.svg" alt="GitHub stars"></a>
</p>

[**English**](/README.md)｜[**简体中文**](/i18n/README.zh.md)｜[**繁體中文**](/i18n/README.zh-TW.md)

**QQ群：875297969**

</div>

## 🌟 專案簡介

VideoLingo 是一站式影片翻譯本地化配音工具，旨在生成 Netflix 級別的高品質字幕，告別生硬機翻，告別多行字幕，還能加上高品質的配音，讓全世界的知識能夠跨越語言的障礙共享。透過直觀的 Streamlit 網頁介面，只需點擊兩下就能完成從影片連結到嵌入高品質雙語字幕甚至帶上配音的整個流程，輕鬆創建 Netflix 品質的本地化影片。

主要特點和功能：
- 🎥 使用 yt-dlp 從 Youtube 連結下載影片

- 🎙️ 使用 WhisperX 進行單字級時間軸字幕辨識

- **📝 使用 NLP 和 GPT 根據句意進行字幕分割**

- **📚 GPT 總結提取術語知識庫，上下文連貫翻譯**

- **🔄 三步直譯、反思、意譯，媲美字幕組精翻效果**

- **✅ 按照 Netflix 標準檢查單行長度，絕無雙行字幕**

- **🗣️ 使用 GPT-SoVITS 等方法對齊配音**

- 🚀 整合包一鍵啟動，在 streamlit 中一鍵出片

- 📝 詳細記錄每步操作日誌，支援隨時中斷和恢復進度

- 🌐 全面的多語言支援，輕鬆實現跨語言影片本地化

與同類專案的主要區別：**絕無多行字幕，最佳的翻譯品質**

## 🎥 效果展示

<table>
<tr>
<td width="33%">

### 俄語翻譯
---
https://github.com/user-attachments/assets/25264b5b-6931-4d39-948c-5a1e4ce42fa7

</td>
<td width="33%">

### GPT-SoVITS
---
https://github.com/user-attachments/assets/47d965b2-b4ab-4a0b-9d08-b49a7bf3508c

</td>
<td width="33%">

### OAITTS
---
https://github.com/user-attachments/assets/85c64f8c-06cf-4af9-b153-ee9d2897b768

</td>
</tr>
</table>

### 語言支援：

當前輸入語言支援和示例：

| 輸入語言 | 支援程度 | 翻譯demo |
|---------|---------|---------|
| 英語 | 🤩 | [英轉中](https://github.com/user-attachments/assets/127373bb-c152-4b7a-8d9d-e586b2c62b4b) |
| 俄語 | 😊 | [俄轉中](https://github.com/user-attachments/assets/25264b5b-6931-4d39-948c-5a1e4ce42fa7) |
| 法語 | 🤩 | [法轉日](https://github.com/user-attachments/assets/3ce068c7-9854-4c72-ae77-f2484c7c6630) |
| 德語 | 🤩 | [德轉中](https://github.com/user-attachments/assets/07cb9d21-069e-4725-871d-c4d9701287a3) |
| 義大利語 | 🤩 | [義轉中](https://github.com/user-attachments/assets/f1f893eb-dad3-4460-aaf6-10cac999195e) |
| 西班牙語 | 🤩 | [西轉中](https://github.com/user-attachments/assets/c1d28f1c-83d2-4f13-a1a1-859bd6cc3553) |
| 日語 | 😐 | [日轉中](https://github.com/user-attachments/assets/856c3398-2da3-4e25-9c36-27ca2d1f68c2) |
| 中文* | 🤩 | [中轉英](https://github.com/user-attachments/assets/48f746fe-96ff-47fd-bd23-59e9202b495c) |
> *中文需單獨配置whisperX模型，僅適用於本地原始碼安裝，配置過程見安裝文檔，並注意在網頁側邊欄指定轉錄語言為zh

翻譯語言支援大模型會的所有語言，配音語言取決於選取的TTS方法。

## 🚀 快速開始

### 線上體驗

只需 5 分鐘即可在 Colab 中快速體驗 VideoLingo：

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Huanshere/VideoLingo/blob/main/VideoLingo_colab.ipynb)

### 本地安裝

VideoLingo 支援所有硬體平台和作業系統，但在 GPU 加速下效能最佳。詳細安裝說明請參考文檔：[English](/docs/pages/docs/start.en-US.md) | [简体中文](/docs/pages/docs/start.zh-CN.md)

### 使用Docker

目前VideoLingo 提供了Dockerfile，可自行使用Dockerfile打包目前VideoLingo，要求CUDA版本為12.4，NVIDIA Driver版本大於550，打包和運行方法為：

```bash
docker build -t videolingo .
docker run -d -p 8501:8501 --gpus all videolingo
```

註：目前 Docker 版本還有一些需要完善的地方，詳情和後續規劃見：[Docker](/docs/pages/docs/docker.zh-CN.md)

## 🏭 批次模式

使用說明: [English](/batch/README.md) | [简体中文](/batch/README.zh.md)

## ⚠️ 當前限制
1. 不同設備運行 whisperX 效果不同，v1.7 會先進行 demucs 人聲分離，但可能會導致分離後轉錄效果不如分離前，原因是 whisper 本身是在帶 bgm 的環境下訓練的，分離前不會轉錄bgm的歌詞，但是分離後可能會轉錄歌詞。

2. **配音功能的品質可能不完美**，仍處於測試開發階段，正在嘗試接入 MascGCT。目前為獲得最佳效果，建議根據原影片的語速和內容特點，選擇相近語速的 TTS，效果見 [demo](https://www.bilibili.com/video/BV1mt1QYyERR/?share_source=copy_web&vd_source=fa92558c28cd668d33dabaddb17e2f9e)。

3. **多語言影片轉錄辨識僅僅只會保留主要語言**，這是由於 whisperX 在強制對齊單字級字幕時使用的是針對單個語言的特化模型，會因為不認識另一種語言而刪去。

3. **多角色分別配音正在開發**，whisperX 具有 VAD 的潛力，但是具體需要一些施工，暫時沒有支援此功能。

## 🚗 路線圖

- [ ] VAD 區分說話人，多角色配音
- [ ] 使用者術語表
- [ ] SaaS 版本
- [ ] 配音影片唇形同步

## 📄 授權條款

本專案採用 Apache 2.0 授權條款。使用本專案時，請遵循以下規定：

1. 發表作品時**建議（不強制要求）標註字幕由 VideoLingo 生成**。
2. 遵循使用的大模型和TTS條約進行備註。
3. 如拷貝程式碼請包含完整的 Apache 2.0 授權條款副本。

我們衷心感謝以下開源專案的貢獻，它們為 VideoLingo 的開發提供了重要支援：

- [whisperX](https://github.com/m-bain/whisperX)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [json_repair](https://github.com/mangiucugna/json_repair)
- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)
- [BELLE](https://github.com/LianjiaTech/BELLE)

## 📬 聯絡我們

- 加入我們的 QQ 群：875297969
- 在 GitHub 上提交 [Issues](https://github.com/Huanshere/VideoLingo/issues) 或 [Pull Requests](https://github.com/Huanshere/VideoLingo/pulls)
- 關注我的 Twitter：[@Huanshere](https://twitter.com/Huanshere)
- 訪問官方網站：[videolingo.io](https://videolingo.io)
- 聯絡郵箱：team@videolingo.io

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo&Timeline)

---

<p align="center">如果覺得 VideoLingo 有幫助，請給我們一個 ⭐️！</p>