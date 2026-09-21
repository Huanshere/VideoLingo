<div align="center">

<img src="/docs/logo.png" alt="VideoLingo Logo" height="140">

# フレームごとに世界をつなぐ

<a href="https://trendshift.io/repositories/12200" target="_blank"><img src="https://trendshift.io/api/badge/repositories/12200" alt="Huanshere%2FVideoLingo | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

[**English**](/README.md)｜[**简体中文**](/translations/README.zh.md)｜[**繁體中文**](/translations/README.zh-TW.md)｜[**日本語**](/translations/README.ja.md)｜[**Español**](/translations/README.es.md)｜[**Русский**](/translations/README.ru.md)｜[**Français**](/translations/README.fr.md)

</div>

## 🌟 概要 ([VLを試す！](https://videolingo.io))

VideoLingo は Streamlit 上で音声認識、字幕翻訳、分割、吹き替えを統合します。字幕ファイルと、必要に応じて字幕付き・吹き替え動画を生成します。翻訳品質は元の音声、言語、選択したモデルに依存します。

主な機能：
- 🎥 yt-dlpによるYouTube動画のダウンロード

- WhisperX による単語単位の音声認識と時間整合

- **📝 NLPとAIを活用した字幕セグメンテーション**

- **📚 一貫性のある翻訳のためのカスタム＋AI生成用語**

- 直訳と、任意の振り返り・自然な書き換え

- 設定可能な文字数制限による字幕分割

- **🗣️ GPT-SoVITS、Azure、OpenAIなどによる吹き替え**

- 🚀 Streamlitでのワンクリック起動と処理

- 🌍 Streamlit UIの多言語サポート

- 📝 進捗再開機能付きの詳細なログ記録

- 🔍 モデル検索セレクター — APIからモデル一覧を自動取得、検索・フィルター対応

- ⏯️ タスクコントロール — 処理中いつでも一時停止・再開・中止が可能

文字起こし、翻訳、字幕レイアウト、吹き替えを一つのプロジェクトで扱います。

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

> *ローカルで中国語を認識する場合は、中国語を明示的に選択すると句読点強化版 Belle Whisper を使用します。

翻訳言語は選択した LLM、吹き替え言語は選択した TTS に依存します。

## インストール

問題がありましたか？無料のオンラインAIエージェントと[**こちら**](https://share.fastgpt.in/chat/share?shareId=066w11n3r9aq6879r4z0v9rh)でチャットして支援を受けられます。

先に [Git](https://git-scm.com/downloads)、[uv](https://docs.astral.sh/uv/getting-started/installation/)、[FFmpeg](https://ffmpeg.org/download.html) をインストールします。ターミナルを開き直し、`git --version`、`uv --version`、`ffmpeg -version` を確認してください。

NVIDIA を使用する場合は、GPU に対応するドライバーが必要です。インストーラーは `nvidia-smi` が CUDA >=12.8 を示す場合に PyTorch `cu128`、それ以外は `cu126` を選択し、NVIDIA がなければ CPU パッケージを選択します。これは Python パッケージの選択であり、システムの CUDA Toolkit は自動インストールしません。WhisperX の GPU 認識には、プロセスから利用できる CUDA 12 cuBLAS と cuDNN 9 も必要です。[GPU 要件](../docs/pages/docs/start.en-US.md#gpu-runtime)を参照してください。

> **注意：** FFmpegが必要です。パッケージマネージャーを使用してインストールしてください：
> - Windows: [FFmpeg ダウンロードページ](https://ffmpeg.org/download.html)の Windows ビルドから**共有ライブラリ版**を選び、`bin` ディレクトリを PATH に追加します。
> - macOS: ```brew install ffmpeg``` ([Homebrew](https://brew.sh/)経由)
> - Linux: ```sudo apt install ffmpeg``` (Debian/Ubuntu)

### uv でインストール

uv が Python 3.13 を取得して `.venv` を作成するため、Python の事前インストールは不要です。アプリは Python 3.10–3.13 に対応します。TorchCodec 0.7 には **FFmpeg 7 共有ライブラリ**を使用してください。FFmpeg 8/9 のみでは非互換です。[検証済み Windows ビルド](../docs/pages/docs/start.en-US.md#ffmpeg-runtime)を参照してください。

1. リポジトリをクローン

```bash
git clone https://github.com/Huanshere/VideoLingo.git
cd VideoLingo
```

2. 環境を作成して依存関係をインストール

```bash
uv run --no-project --python 3.13 setup_env.py
```

3. アプリケーションの起動

```bash
.venv\Scripts\streamlit run st.py        # Windows
.venv/bin/streamlit run st.py            # macOS / Linux
```

Windows では `OneKeyStart.bat` をダブルクリックすることもできます。既存の `~/.venvs/videolingo` を優先し、次にプロジェクトの `.venv` を使用します。`http://localhost:8501` を開き、サイドバーで API URL、キー、モデルを設定してください。

### Docker
Linux の NVIDIA コンテナーには Docker、互換ドライバー、[NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) が必要です。イメージは同じ Python 3.13 セットアップとアプリ依存関係を使用し、既定は CUDA 12.8.1/cu128 です。CUDA 12.6 の組み合わせとデータ永続化は [Docker ドキュメント](/docs/pages/docs/docker.en-US.md)を参照してください。

```bash
docker build -t videolingo .
docker run -d -p 8501:8501 --gpus all videolingo
```

## API
VideoLingoはOpenAIライクなAPI形式と様々なTTSインターフェースをサポートしています：
- LLM: OpenAI Chat Completions 互換で、処理に必要な構造化 JSON を返せるサービスとモデルを選びます。API URL、キー、モデルはサイドバーで設定します。
- 音声認識：ローカル WhisperX または ElevenLabs API。
- TTS: Azure、OpenAI、Fish TTS、SiliconFlow Fish/CosyVoice2、GPT-SoVITS、Edge TTS、F5-TTS、および `core/tts_backend/custom_tts.py` のカスタムアダプター。

詳細なインストール方法、API設定、バッチモードの説明については、ドキュメントを参照してください：[English](/docs/pages/docs/start.en-US.md) | [中文](/docs/pages/docs/start.zh-CN.md)

## 現在の制限事項

1. 背景雑音と言語別の整合モデルは、認識と単語の時刻に影響します。音声分離が役立つ場合があります。数字や記号の時刻は不確かな場合があるため、生成字幕を確認してください。

2. 応答は必要な JSON 構造を満たす必要があります。失敗時は `output/gpt_log/error.json` を確認してください。成功した応答のキャッシュや完了済み出力は再利用されるため、モデル変更だけでは全工程を再生成しません。最初から全出力を削除しないでください。

3. 吹き替えの品質とタイミングは翻訳、TTS、発話速度に依存します。速度調整で自然さや完全な同期が保証されるわけではありません。

4. ローカル WhisperX は各区間で一つの認識・整合言語を使用します。複数言語が混ざる音声では、すべての言語の文字と時刻が正確になる保証はありません。

5. 吹き替え処理は、話者ごとに異なる声を自動割り当てしません。

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
