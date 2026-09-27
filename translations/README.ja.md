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

- Qwen3-ASR + Qwen3-ForcedAligner による単語単位の音声認識と時間整合

- **📝 NLPとAIを活用した字幕セグメンテーション**

- **📚 一貫性のある翻訳のためのカスタム＋AI生成用語**

- 直訳と、任意の振り返り・自然な書き換え

- 設定可能な文字数制限による字幕分割

- **🗣️ GPT-SoVITS、OpenAI、Edge TTSなどによる吹き替え**

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

🇺🇸 英語 🤩 | 🇷🇺 ロシア語 😊 | 🇫🇷 フランス語 🤩 | 🇩🇪 ドイツ語 🤩 | 🇮🇹 イタリア語 🤩 | 🇪🇸 スペイン語 🤩 | 🇯🇵 日本語 😊 | 🇨🇳 中国語 🤩

吹き替え言語は選択した TTS に依存します。

## インストール

VideoLingo は Windows、macOS（Apple Silicon / Intel）、Linux に対応しています。

### ローカル AI エージェントに頼む 🤖

AI エージェントがこのコンピューターを操作できる場合は、次のように伝えてください。

> GitHub の Huanshere/VideoLingo をこのコンピューターにインストールして起動して。

### Windows：ダブルクリックでインストール 🎉

1. [最新リリース](https://github.com/Huanshere/VideoLingo/releases/latest)から **Source code (zip)** をダウンロードし、デスクトップなどに展開してフォルダーを開きます。
2. `OneKeyStart.bat` をダブルクリックし、ウィンドウを開いたままにします。初回は uv、Python 3.12、アプリの依存関係、FFmpeg を自動でインストールします。インターネット接続が必要です。
3. インストールが完了すると、VideoLingo がブラウザーで自動的に開きます。サイドバーに API URL、キー、モデルを入力して使い始めてください。

### ソースコードからインストール（Windows・macOS・Linux）

```bash
git clone https://github.com/Huanshere/VideoLingo.git && cd VideoLingo
uv run start.py
```

次回からは VideoLingo フォルダーで `uv run start.py` を実行します。Apple Silicon は MLX、Intel Mac は CPU で音声認識を行います。Intel Mac の吹き替えでは、既定で元動画の背景音は残らず、新しい音声のみを使用します。

#### Docker（オプション）

Linux の NVIDIA コンテナーには Docker、互換ドライバー、[NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) が必要です。イメージは同じ Python 3.12 セットアップとアプリ依存関係を使用し、既定は CUDA 12.8.1/cu128 です。CUDA 12.6 の組み合わせとデータ永続化は [Docker ドキュメント](/docs/pages/docs/docker.en-US.md)を参照してください。

```bash
docker build -t videolingo .
docker run -d -p 8501:8501 --gpus all videolingo
```

## API
VideoLingoはOpenAIライクなAPI形式と様々なTTSインターフェースをサポートしています：
- LLM: OpenAI Chat Completions 互換で、処理に必要な構造化 JSON を返せるサービスとモデルを選びます。API URL、キー、モデルはサイドバーで設定します。
- 音声認識：ローカル Qwen3-ASR + ForcedAligner（既定）、または ElevenLabs API。インストーラーは WhisperX を入れません。バックエンドとして使う場合は [WhisperX（手動インストール）](../docs/pages/docs/whisperx-manual.en-US.md) を参照してください。
- TTS: OpenAI、Fish TTS、SiliconFlow Fish/CosyVoice2、GPT-SoVITS、Edge TTS、F5-TTS、および `core/tts_backend/custom_tts.py` のカスタムアダプター。

詳細なインストール方法、API設定、バッチモードの説明については、ドキュメントを参照してください：[English](/docs/pages/docs/start.en-US.md) | [中文](/docs/pages/docs/start.zh-CN.md)

## 現在の制限事項

1. 背景雑音と言語別の整合モデルは、認識と単語の時刻に影響します。音声分離が役立つ場合があります。数字や記号の時刻は不確かな場合があるため、生成字幕を確認してください。

2. 応答は必要な JSON 構造を満たす必要があります。失敗時は `output/gpt_log/error.json` を確認してください。成功した応答のキャッシュや完了済み出力は再利用されるため、モデル変更だけでは全工程を再生成しません。最初から全出力を削除しないでください。

3. 吹き替えの品質とタイミングは翻訳、TTS、発話速度に依存します。速度調整で自然さや完全な同期が保証されるわけではありません。

4. ローカル認識は各音声区間で一つの主要な認識・整合言語を使用します。複数言語が混ざる音声では、すべての言語の文字と時刻が正確になる保証はありません。

5. 吹き替え処理は、話者ごとに異なる声を自動割り当てしません。

## 📄 ライセンス

このプロジェクトはApache 2.0ライセンスの下で提供されています。以下のオープンソースプロジェクトの貢献に特別な感謝を表します：

[Qwen3-ASR](https://github.com/Qwen/Qwen3-ASR), [MLX Audio](https://github.com/Blaizzy/mlx-audio), [whisperX](https://github.com/m-bain/whisperX), [yt-dlp](https://github.com/yt-dlp/yt-dlp), [json_repair](https://github.com/mangiucugna/json_repair), [BELLE](https://github.com/LianjiaTech/BELLE)

## 📬 お問い合わせ

- GitHubで[Issues](https://github.com/Huanshere/VideoLingo/issues)や[Pull Requests](https://github.com/Huanshere/VideoLingo/pulls)を提出
- Twitter: [@Huanshere](https://twitter.com/Huanshere)でDM
- メール: team@videolingo.io

## ⭐ スター履歴

[![Star History Chart](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo&Timeline)

---

<p align="center">VideoLingoが役立つと感じた場合は、⭐️をお願いします！</p>
