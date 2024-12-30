<div align="center">

<img src="/docs/logo.png" alt="VideoLingo Logo" height="140">

# 世界をつなぐ、フレームごとに

[Website](https://videolingo.io) | [Documentation](https://docs.videolingo.io/docs/start)

[**English**](../README.md)｜[**中文**](./README.zh.md)｜[**日本語**](./README.ja.md)

</div>

## 🌟 概要（[無料でVideoLingoを試す！](https://videolingo.io)）

VideoLingoは、Netflix品質の字幕を生成することを目的とした、オールインワンのビデオ翻訳、ローカリゼーション、および吹き替えツールです。硬直した機械翻訳や複数行の字幕を排除し、高品質の吹き替えを追加することで、言語の壁を越えたグローバルな知識共有を可能にします。

主な機能：
- 🎥 yt-dlpを使用したYouTubeビデオのダウンロード

- **🎙️ WhisperXによる単語レベルおよび低幻覚の字幕認識**

- **📝 NLPおよびAIによる字幕のセグメンテーション**

- **📚 一貫した翻訳のためのカスタム+AI生成の用語集**

- **🔄 映画品質のための3ステップの翻訳-反映-適応**

- **✅ Netflix標準、単一行の字幕のみ**

- **🗣️ GPT-SoVITS、Azure、OpenAIなどによる吹き替え**

- 🚀 Streamlitでのワンクリック起動と処理

- 📝 進行状況の再開をサポートする詳細なログ記録

類似プロジェクトとの違い：**単一行の字幕のみ、優れた翻訳品質、シームレスな吹き替え体験**

## 🎥 デモ

<table>
<tr>
<td width="50%">

### ロシア語翻訳
---
https://github.com/user-attachments/assets/25264b5b-6931-4d39-948c-5a1e4ce42fa7

</td>
<td width="50%">

### GPT-SoVITS吹き替え
---
https://github.com/user-attachments/assets/47d965b2-b4ab-4a0b-9d08-b49a7bf3508c

</td>
</tr>
</table>

### 言語サポート

**入力言語サポート（今後追加予定）：**

🇺🇸 英語 🤩 | 🇷🇺 ロシア語 😊 | 🇫🇷 フランス語 🤩 | 🇩🇪 ドイツ語 🤩 | 🇮🇹 イタリア語 🤩 | 🇪🇸 スペイン語 🤩 | 🇯🇵 日本語 😐 | 🇨🇳 中国語* 😊

> *中国語は現在、別の句読点強化されたwhisperモデルを使用しています...

**翻訳はすべての言語をサポートし、吹き替え言語は選択したTTSメソッドに依存します。**

## インストール

> **注意:** WindowsでNVIDIA GPUアクセラレーションを使用するには、以下の手順を完了してください：
> 1. [CUDA Toolkit 12.6](https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe)をインストール
> 2. [CUDNN 9.3.0](https://developer.download.nvidia.com/compute/cudnn/9.3.0/local_installers/cudnn_9.3.0_windows.exe)をインストール
> 3. `C:\Program Files\NVIDIA\CUDNN\v9.3\bin\12.6`をシステムPATHに追加
> 4. コンピュータを再起動

> **注意:** FFmpegが必要です。パッケージマネージャーを使用してインストールしてください：
> - Windows: ```choco install ffmpeg``` (via [Chocolatey](https://chocolatey.org/))
> - macOS: ```brew install ffmpeg``` (via [Homebrew](https://brew.sh/))
> - Linux: ```sudo apt install ffmpeg``` (Debian/Ubuntu) or ```sudo dnf install ffmpeg``` (Fedora)

1. リポジトリをクローン

```bash
git clone https://github.com/Huanshere/VideoLingo.git
cd VideoLingo
```

2. 依存関係をインストール（`python=3.10`が必要）

```bash
conda create -n videolingo python=3.10.0 -y
conda activate videolingo
python install.py
```

3. アプリケーションを起動

```bash
streamlit run st.py
```

### Docker
また、Dockerを使用することもできます（CUDA 12.4およびNVIDIA Driverバージョン>550が必要）、[Dockerドキュメント](/docs/pages/docs/docker.en-US.md)を参照してください：

```bash
docker build -t videolingo .
docker run -d -p 8501:8501 --gpus all videolingo
```

## API
VideoLingoはOpenAI-Like API形式およびさまざまな吹き替えインターフェースをサポートしています：
- `claude-3-5-sonnet-20240620`, **`gemini-2.0-flash-exp`**, `gpt-4o`, `deepseek-coder`, ...（パフォーマンス順）
- `azure-tts`, `openai-tts`, `siliconflow-fishtts`, **`fish-tts`**, `GPT-SoVITS`, `edge-tts`, `*custom-tts`（custom_tts.pyで定義するためにgptに依頼）

> **注意:** VideoLingoは現在、[302.ai](https://gpt302.saaslink.net/C2oHR9)と統合されており、**1つのAPI KEY**でLLMとTTSの両方をサポートします！また、OllamaをLLMとして使用し、Edge-TTSを吹き替えとして使用する完全なローカルデプロイメントもサポートしています。クラウドAPIは不要です！

詳細なインストール、API構成、およびバッチモードの手順については、ドキュメントを参照してください：[English](/docs/pages/docs/start.en-US.md) | [中文](/docs/pages/docs/start.zh-CN.md)

## 現在の制限

1. WhisperXの転写パフォーマンスは、wav2vacモデルを使用してアライメントを行うため、ビデオのバックグラウンドノイズの影響を受ける可能性があります。バックグラウンドミュージックが大きいビデオの場合は、ボイスセパレーションエンハンスメントを有効にしてください。さらに、数字や特殊文字で終わる字幕は、wav2vacが数値文字（例："1"）をその発音形式（例："one"）にマッピングできないため、早期に切り捨てられる可能性があります。

2. 弱いモデルを使用すると、応答のJSON形式の要件が厳しいため、中間プロセス中にエラーが発生する可能性があります。このエラーが発生した場合は、`output`フォルダを削除し、別のLLMで再試行してください。そうしないと、繰り返し実行すると前回の誤った応答が読み込まれ、同じエラーが発生します。

3. 吹き替え機能は、言語間の話速やイントネーションの違い、および翻訳ステップの影響により、100％完璧ではない可能性があります。ただし、このプロジェクトでは、最良の吹き替え結果を確保するために、話速に関する広範なエンジニアリング処理が実装されています。

4. **多言語ビデオの転写認識は、主要言語のみを保持します**。これは、whisperXが単語レベルの字幕を強制的にアライメントする際に、単一言語用の特化モデルを使用し、認識されない言語を削除するためです。

5. **複数のキャラクターを個別に吹き替えることはできません**。whisperXの話者区別機能は十分に信頼できません。

## 📄 ライセンス

このプロジェクトはApache 2.0ライセンスの下でライセンスされています。以下のオープンソースプロジェクトの貢献に特に感謝します：

[whisperX](https://github.com/m-bain/whisperX), [yt-dlp](https://github.com/yt-dlp/yt-dlp), [json_repair](https://github.com/mangiucugna/json_repair), [BELLE](https://github.com/LianjiaTech/BELLE)

## 📬 お問い合わせ

- Discordに参加：https://discord.gg/9F2G92CWPp
- GitHubで[Issues](https://github.com/Huanshere/VideoLingo/issues)または[Pull Requests](https://github.com/Huanshere/VideoLingo/pulls)を提出
- Twitterでフォロー：[Huanshere](https://twitter.com/Huanshere)
- メールで連絡：team@videolingo.io

## ⭐ スター履歴

[![Star History Chart](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo&Timeline)

---

<p align="center">VideoLingoが役に立ったと思ったら、ぜひ⭐️をください！</p>
