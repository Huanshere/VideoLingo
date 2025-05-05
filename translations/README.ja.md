<div align="center">

<img src="/docs/logo.png" alt="VideoLingo Logo" height="140">

# フレームごとに世界をつなぐ

<a href="https://trendshift.io/repositories/12200" target="_blank"><img src="https://trendshift.io/api/badge/repositories/12200" alt="Huanshere%2FVideoLingo | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

[**English**](/README.md)｜[**简体中文**](/translations/README.zh.md)｜[**繁體中文**](/translations/README.zh-TW.md)｜[**日本語**](/translations/README.ja.md)｜[**Español**](/translations/README.es.md)｜[**Русский**](/translations/README.ru.md)｜[**Français**](/translations/README.fr.md)

</div>

## 🌟 概要 ([VLを試す！](https://videolingo.io))

VideoLingoは、Netflixクオリティの字幕を生成することを目的とした、オールインワンの動画翻訳、ローカライゼーション、吹き替えツールです。機械的な翻訳や複数行の字幕を排除し、高品質な吹き替えを追加することで、言語の壁を越えた世界的な知識共有を可能にします。

主な機能：
- 🎥 yt-dlpによるYouTube動画のダウンロード

- **🎙️ WhisperXによる単語レベルの低誤認識字幕認識**

- **📝 NLPとAIを活用した字幕セグメンテーション**

- **📚 一貫性のある翻訳のためのカスタム＋AI生成用語**

- **🔄 映画品質のための3ステップ（翻訳-反映-適応）プロセス**

- **✅ Netflixスタンダードの1行字幕のみ**

- **🗣️ GPT-SoVITS、Azure、OpenAIなどによる吹き替え**

- 🚀 Streamlitでのワンクリック起動と処理

- 🌍 Streamlit UIの多言語サポート

- 📝 進捗再開機能付きの詳細なログ記録

類似プロジェクトとの違い：**1行字幕のみ、優れた翻訳品質、シームレスな吹き替え体験**

## 🎥 デモ

<table>
<tr>
<td width="33%">

### デュアル字幕
---
https://github.com/user-attachments/assets/a5c3d8d1-2b29-4ba9-b0d0-25896829d951

</td>
<td width="33%">

### Cosy2 ボイスクローン
---
https://github.com/user-attachments/assets/e065fe4c-3694-477f-b4d6-316917df7c0a

</td>
<td width="33%">

### GPT-SoVITS 吹き替え
---
https://github.com/user-attachments/assets/47d965b2-b4ab-4a0b-9d08-b49a7bf3508c

</td>
</tr>
</table>

### 言語サポート

**入力言語サポート（今後追加予定）：**

🇺🇸 英語 🤩 | 🇷🇺 ロシア語 😊 | 🇫🇷 フランス語 🤩 | 🇩🇪 ドイツ語 🤩 | 🇮🇹 イタリア語 🤩 | 🇪🇸 スペイン語 🤩 | 🇯🇵 日本語 😐 | 🇨🇳 中国語* 😊

> *中国語は現在、句読点強化されたwhisperモデルを使用しています。

**翻訳はすべての言語に対応していますが、吹き替えの言語は選択したTTS方式によって異なります。**

## インストール

問題がありましたか？無料のオンラインAIエージェントと[**こちら**](https://share.fastgpt.in/chat/share?shareId=066w11n3r9aq6879r4z0v9rh)でチャットして支援を受けられます。

> **注意：** NVIDIA GPUを搭載したWindowsユーザーは、インストール前に以下の手順を実行してください：
> 1. [CUDA Toolkit 12.6](https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe)をインストール
> 2. [CUDNN 9.3.0](https://developer.download.nvidia.com/compute/cudnn/9.3.0/local_installers/cudnn_9.3.0_windows.exe)をインストール
> 3. `C:\Program Files\NVIDIA\CUDNN\v9.3\bin\12.6`をシステムPATHに追加
> 4. コンピュータを再起動

> **注意：** FFmpegが必要です。パッケージマネージャーを使用してインストールしてください：
> - Windows: ```choco install ffmpeg``` ([Chocolatey](https://chocolatey.org/)経由)
> - macOS: ```brew install ffmpeg``` ([Homebrew](https://brew.sh/)経由)
> - Linux: ```sudo apt install ffmpeg``` (Debian/Ubuntu)

1. リポジトリをクローン

```bash
git clone https://github.com/Huanshere/VideoLingo.git
cd VideoLingo
```

2. 依存関係のインストール（`python=3.10`が必要）

```bash
conda create -n videolingo python=3.10.0 -y
conda activate videolingo
python install.py
```

3. アプリケーションの起動

```bash
streamlit run st.py
```

### Docker
または、Docker（CUDA 12.4とNVIDIAドライバーバージョン>550が必要）を使用することもできます。[Dockerドキュメント](/docs/pages/docs/docker.en-US.md)を参照してください：

```bash
docker build -t videolingo .
docker run -d -p 8501:8501 --gpus all videolingo
```

## API
VideoLingoはOpenAIライクなAPI形式と様々なTTSインターフェースをサポートしています：
- LLM: `claude-3-5-sonnet`, `gpt-4.1`, `deepseek-v3`, `gemini-2.0-flash`, ... (パフォーマンス順、gemini-2.5-flashには注意...)
- WhisperX: ローカルでwhisperXを実行するか302.ai APIを使用
- TTS: `azure-tts`, `openai-tts`, `siliconflow-fishtts`, **`fish-tts`**, `GPT-SoVITS`, `edge-tts`, `*custom-tts`(custom_tts.pyで独自のTTSを修正可能！)

> **注意：** VideoLingoは**[302.ai](https://gpt302.saaslink.net/C2oHR9)**と連携しています - すべてのサービス（LLM、WhisperX、TTS）に1つのAPIキーで対応。またはOllamaとEdge-TTSを使用してローカルで無料で実行可能で、APIは不要です！

詳細なインストール方法、API設定、バッチモードの説明については、ドキュメントを参照してください：[English](/docs/pages/docs/start.en-US.md) | [中文](/docs/pages/docs/start.zh-CN.md)

## 現在の制限事項

1. WhisperX文字起こしのパフォーマンスは、アライメントにwav2vacモデルを使用しているため、動画の背景ノイズの影響を受ける可能性があります。大きな背景音楽がある動画の場合は、音声分離強化を有効にしてください。また、wav2vacが数字文字（例：「1」）を発話形式（「one」）にマッピングできないため、数字や特殊文字で終わる字幕は早期に切り捨てられる可能性があります。

2. より弱いモデルを使用すると、レスポンスに厳密なJSON形式が要求されるため、中間プロセスでエラーが発生する可能性があります。このエラーが発生した場合は、`output`フォルダを削除して別のLLMで再試行してください。そうしないと、繰り返し実行時に前回の誤ったレスポンスを読み込んで同じエラーが発生します。

3. 吹き替え機能は、言語間の発話速度やイントネーションの違い、および翻訳ステップの影響により、100%完璧ではない可能性があります。ただし、このプロジェクトでは発話速度に関する広範なエンジニアリング処理を実装し、可能な限り最高の吹き替え結果を確保しています。

4. **多言語ビデオの文字起こし認識は主要言語のみを保持します**。これは、whisperXが単語レベルの字幕を強制的にアライメントする際に単一言語用の特殊モデルを使用し、認識されない言語を削除するためです。

5. **複数のキャラクターを個別に吹き替えることはできません**。これは、whisperXの話者区別機能が十分に信頼できないためです。

## 📄 ライセンス

このプロジェクトはApache 2.0ライセンスの下で提供されています。以下のオープンソースプロジェクトの貢献に特別な感謝を表します：

[whisperX](https://github.com/m-bain/whisperX), [yt-dlp](https://github.com/yt-dlp/yt-dlp), [json_repair](https://github.com/mangiucugna/json_repair), [BELLE](https://github.com/LianjiaTech/BELLE)

## 📬 お問い合わせ

- GitHubで[Issues](https://github.com/Huanshere/VideoLingo/issues)や[Pull Requests](https://github.com/Huanshere/VideoLingo/pulls)を提出
- Twitter: [@Huanshere](https://twitter.com/Huanshere)でDM
- メール: team@videolingo.io

## ⭐ スター履歴

[![Star History Chart](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo&Timeline)

---

<p align="center">VideoLingoが役立つと感じた場合は、⭐️をお願いします！</p> 