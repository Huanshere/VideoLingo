<div align="center">

<img src="https://s21.ax1x.com/2024/09/29/pA16WHx.png" alt="VideoLingo Logo" height="140">

# VideoLingo: 世界をつなぐ一コマ一コマ
<p align="center">
  <a href="https://www.python.org" target="_blank"><img src="https://img.shields.io/badge/Python-3.10-blue.svg" alt="Python"></a>
  <a href="https://github.com/Huanshere/VideoLingo/blob/main/LICENSE" target="_blank"><img src="https://img.shields.io/github/license/Huanshere/VideoLingo.svg" alt="License"></a>
  <a href="https://github.com/Huanshere/VideoLingo/stargazers" target="_blank"><img src="https://img.shields.io/github/stars/Huanshere/VideoLingo.svg" alt="GitHub stars"></a>
  <a href="https://colab.research.google.com/github/Huanshere/VideoLingo/blob/main/VideoLingo_colab.ipynb" target="_blank"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a>
</p>

[**中文**](README.md) | [**English**](README.en.md)｜[**日本語**](README.ja.md)

**QQグループ：875297969**

</div>

## 🌟 プロジェクト紹介

VideoLingoは、Netflix品質の高品質な字幕を生成し、硬直した機械翻訳や多行字幕を排除し、高品質な吹き替えも追加することを目的としたオールインワンのビデオ翻訳ローカリゼーションツールです。これにより、世界中の知識が言語の壁を越えて共有されることが可能になります。直感的なStreamlitウェブインターフェースを通じて、ビデオリンクから高品質なバイリンガル字幕を埋め込んだり、吹き替えを追加したりするプロセスを数回のクリックで完了し、Netflix品質のローカライズビデオを簡単に作成できます。

主な特徴と機能：
- 🎥 yt-dlpを使用してYouTubeリンクからビデオをダウンロード

- 🎙️ WhisperXを使用して単語レベルのタイムライン字幕認識を行う

- **📝 NLPとGPTを使用して文の意味に基づいて字幕を分割**

- **📚 GPTが用語知識ベースを要約し、文脈に基づいた翻訳を実現**

- **🔄 直訳、反省、意訳の三段階で、プロの字幕翻訳品質に匹敵**

- **✅ Netflix標準に従って単行の長さをチェックし、絶対に二行字幕はなし**

- **🗣️ GPT-SoVITSなどの方法を使用して高品質な吹き替えを行う**

- 🚀 ワンクリックで統合パッケージを起動し、Streamlitでワンクリックでビデオを作成

- 📝 各操作ステップの詳細なログを記録し、いつでも中断と進行の再開をサポート

- 🌐 包括的な多言語サポートにより、簡単にクロスランゲージビデオローカリゼーションを実現

同類のプロジェクトとの主な違い：**絶対に多行字幕はなし、最高の翻訳品質**

## 🎥 デモ

<table>
<tr>
<td width="25%">

### ロシア語翻訳
---
https://github.com/user-attachments/assets/25264b5b-6931-4d39-948c-5a1e4ce42fa7

</td>
<td width="25%">

### GPT-SoVITS
---
https://github.com/user-attachments/assets/47d965b2-b4ab-4a0b-9d08-b49a7bf3508c

</td>
<td width="25%">

### Fish TTS 丁真
---
https://github.com/user-attachments/assets/e7bb9090-d2ef-4261-9dc5-56bd67dc710d

</td>
<td width="25%">

### OAITTS
---
https://github.com/user-attachments/assets/85c64f8c-06cf-4af9-b153-ee9d2897b768

</td>
</tr>
</table>

### 言語サポート：

現在サポートされている入力言語と例：

| 入力言語 | サポートレベル | 翻訳デモ | 吹き替えデモ |
|---------|---------|---------|----------|
| 英語 | 🤩 | [英語から中国語](https://github.com/user-attachments/assets/127373bb-c152-4b7a-8d9d-e586b2c62b4b) | TODO |
| ロシア語 | 😊 | [ロシア語から中国語](https://github.com/user-attachments/assets/25264b5b-6931-4d39-948c-5a1e4ce42fa7) | TODO |
| フランス語 | 🤩 | [フランス語から日本語](https://github.com/user-attachments/assets/3ce068c7-9854-4c72-ae77-f2484c7c6630) | TODO |
| ドイツ語 | 🤩 | [ドイツ語から中国語](https://github.com/user-attachments/assets/07cb9d21-069e-4725-871d-c4d9701287a3) | TODO |
| イタリア語 | 🤩 | [イタリア語から中国語](https://github.com/user-attachments/assets/f1f893eb-dad3-4460-aaf6-10cac999195e) | TODO |
| スペイン語 | 🤩 | [スペイン語から中国語](https://github.com/user-attachments/assets/c1d28f1c-83d2-4f13-a1a1-859bd6cc3553) | TODO |
| 日本語 | 😐 | [日本語から中国語](https://github.com/user-attachments/assets/856c3398-2da3-4e25-9c36-27ca2d1f68c2) | TODO |
| 中国語* | 🤩 | [中国語から英語](https://github.com/user-attachments/assets/48f746fe-96ff-47fd-bd23-59e9202b495c) | [羅翔先生のトークショー](https://github.com/user-attachments/assets/85c64f8c-06cf-4af9-b153-ee9d2897b768) |
> *中国語はwhisperXモデルの別途設定が必要です。詳細はソースコードのインストールを参照し、ウェブページのサイドバーで転写言語をzhに指定してください。

翻訳言語は大規模言語モデルが対応するすべての言語をサポートし、吹き替え言語は選択したTTS方法に依存します。

## 🚀 Windows用ワンクリック統合パッケージ

### 注意事項：

1. 統合パッケージはCPUバージョンのtorchを使用しており、サイズは約**2.6G**です。
2. 吹き替えステップでUVR5を使用して音声分離を行う場合、CPUバージョンはGPU加速のtorchよりも著しく遅くなります。
3. 統合パッケージは**APIを介してwhisperXapi ☁️を呼び出すことのみをサポート**し、ローカルでwhisperXを実行することはサポートしていません💻。
4. 統合パッケージで使用されるwhisperXapiは中国語の転写をサポートしていません。中国語を使用する必要がある場合は、ソースコードからインストールし、ローカルでwhisperXを実行してください💻。
5. 統合パッケージは転写ステップでUVR5音声分離をまだ行っていないため、BGMが騒がしいビデオの使用は推奨されません。

以下の機能が必要な場合は、ソースコードからインストールしてください（Nvidia GPUと少なくとも**20G**のディスクスペースが必要です）：
- 入力言語が中国語
- ローカルでwhisperXを実行💻
- GPU加速のUVR5を使用して音声分離
- BGMが騒がしいビデオの転写

### ダウンロードと使用方法

1. `v1.4`ワンクリックパッケージ（800M）をダウンロード：[直接ダウンロード](https://vip.123pan.cn/1817874751/8209290) | [Baiduバックアップ](https://pan.baidu.com/s/1H_3PthZ3R3NsjS0vrymimg?pwd=ra64)

2. 解凍後、フォルダ内の`一键启动.bat`をダブルクリックして実行

3. 開いたブラウザウィンドウで、サイドバーで必要な設定を行い、ワンクリックでビデオを作成！
  ![attention](https://github.com/user-attachments/assets/7db25130-d421-452e-a16a-d7cfb0478ebf)


> 💡 ヒント: 本プロジェクトは大規模言語モデル、WhisperX、TTSの設定が必要です。以下の**API準備**セクションを注意深くお読みください

## 📋 API準備
本プロジェクトは大規模言語モデル、WhisperX、TTSの使用が必要です。各コンポーネントには複数のオプションが提供されています。**設定ガイドを注意深くお読みください😊**
### 1. **大規模言語モデルのAPI_KEYを取得**：

| 推奨モデル | 推奨プロバイダー | base_url | 価格 | 効果 |
|:-----|:---------|:---------|:-----|:---------|
| claude-3-5-sonnet-20240620（デフォルト） | [雲霧api](https://yunwu.zeabur.app/register?aff=TXMB) | https://yunwu.zeabur.app | ￥15 / 1M tokens | 🤩 |
| deepseek-coder | [deepseek](https://platform.deepseek.com/api_keys) | https://api.deepseek.com | ￥2 / 1M tokens | 😲 |
> 注：雲霧apiはopenaiのtts-1インターフェースもサポートしており、吹き替えステップで使用できます。

> リマインダー：deepseekは翻訳中に非常に低い確率でエラーが発生する可能性があります。エラーが発生した場合は、claude 3.5 sonnetモデルに切り替えてください。

#### よくある質問

<details>
<summary>どのモデルを選ぶべきですか？</summary>

- 🌟 デフォルトでClaude 3.5を使用し、翻訳品質が非常に優れており、連続性が非常に良く、AIの味がありません。
- 🚀 deepseekを使用する場合、1時間のビデオの翻訳には約￥1がかかり、結果は平均的です。
</details>

<details>
<summary>APIキーを取得する方法は？</summary>

1. 上記の推奨プロバイダーのリンクをクリック
2. アカウントを登録し、チャージ
3. APIキーのページで新しいAPIキーを作成
4. 雲霧apiの場合、`無制限のクォータ`をチェックし、`claude-3-5-sonnet-20240620`モデルを選択し、`純AZ 1.5倍`チャネルを選択することをお勧めします。
</details>

<details>
<summary>他のモデルを使用できますか？</summary>

- ✅ OAI-Like APIインターフェースをサポートしていますが、Streamlitのサイドバーで自分で変更する必要があります。
- ⚠️ ただし、他のモデル（特に小さなモデル）は指示に従う能力が弱く、翻訳中にエラーが発生する可能性が非常に高いため、強くお勧めしません。
</details>

### 2. **Replicateのトークンを準備**（whisperXapi ☁️を使用する場合のみ）

VideoLingoはWhisperXを使用して音声認識を行い、ローカルデプロイメントとクラウドAPIの両方をサポートしています。
#### オプションの比較：
| オプション | 欠点 |
|:-----|:-----|
| **whisperX 🖥️** | • CUDAのインストール 🛠️<br>• モデルのダウンロード 📥<br>• 高いVRAM要件 💾 |
| **whisperXapi ☁️** | • VPNが必要 🕵️‍♂️<br>• Visaカード 💳<br>• **中国語の効果が悪い** 🚫 |

#### トークンの取得
   - [Replicate](https://replicate.com/account/api-tokens)に登録し、Visaカードの支払い方法をバインドしてトークンを取得
   - **またはQQグループに参加し、グループのアナウンスから無料のテストトークンを取得**

### 3. **TTSのAPI**
VideoLingoは複数のTTS統合方法を提供しています。以下は比較です（吹き替えを使用せず、翻訳のみの場合はスキップしてください）：

| TTSオプション | 利点 | 欠点 | 中国語の効果 | 非中国語の効果 |
|:---------|:-----|:-----|:---------|:-----------|
| 🎙️ OpenAI TTS | 感情がリアル | 中国語は外国人のように聞こえる | 😕 | 🤩 |
| 🔊 Azure TTS (推奨)  | 自然な効果 | チャージが不便 | 🤩 | 😃 |
| 🎤 Fish TTS  | 優れた効果 | チャージが必要 時々不安定 | 😱 | 😱 |
| 🗣️ GPT-SoVITS (テスト) | ローカルでの音声クローン | 現在、英語入力中国語出力のみをサポートしており、Nカードでのモデル推論が必要で、明確なBGMのない単一人物のビデオに最適で、ベースモデルは元の声に近い必要があります | 😂 | 🚫 |

- OpenAI TTSの場合、[雲霧api](https://yunwu.zeabur.app/register?aff=TXMB)を使用することをお勧めします。
- **Azure TTSの無料キーはQQグループのアナウンスで取得できます** または[公式サイト](https://learn.microsoft.com/zh-cn/azure/ai-services/speech-service/get-started-text-to-speech?tabs=windows%2Cterminal&pivots=programming-language-python)で自分で登録してチャージできます。
- **Fish TTSの無料キーはQQグループのアナウンスで取得できます** または[公式サイト](https://fish.audio/zh-CN/go-api/)で自分で登録してチャージできます。

<details>
<summary>OpenAIの声を選ぶ方法は？</summary>

声のリストは[公式サイト](https://platform.openai.com/docs/guides/text-to-speech/voice-options)で見つけることができます。例えば、`alloy`、`echo`、`nova`、`fable`などです。`config.py`で`OAI_VOICE`を変更して声を変更します。

</details>
<details>
<summary>Azureの声を選ぶ方法は？</summary>

[オンライン体験](https://speech.microsoft.com/portal/voicegallery)で聞いて選びたい声を選び、右側のコードでその声に対応するコードを見つけることをお勧めします。例えば、`zh-CN-XiaoxiaoMultilingualNeural`です。

</details>

<details>
<summary>Fish TTSの声を選ぶ方法は？</summary>

[公式サイト](https://fish.audio/zh-CN/)で聞いて選びたい声を選び、その声に対応するコードをURLで見つけます。例えば、丁真は`54a5170264694bfc8e9ad98df7bd89c3`です。人気のある声は`config.py`に追加されており、`FISH_TTS_CHARACTER`を変更するだけです。他の声を使用する必要がある場合は、`config.py`で`FISH_TTS_CHARACTER_ID_DICT`辞書を変更してください。

</details>

<details>
<summary>GPT-SoVITS-v2の使用チュートリアル</summary>

1. [公式のYuqueドキュメント](https://www.yuque.com/baicaigongchang1145haoyuangong/ib3g1e/dkxgpiy9zb96hob4#KTvnO)にアクセスして、構成要件を確認し、統合パッケージをダウンロードします。

2. `GPT-SoVITS-v2-xxx`を`VideoLingo`と同じディレクトリレベルに配置します。**注意：並列フォルダである必要があります。**

3. 次の方法のいずれかを選択してモデルを構成します：

   a. 自分でトレーニングしたモデル：
   - モデルをトレーニングした後、`GPT-SoVITS-v2-xxx\GPT_SoVITS\configs`の`tts_infer.yaml`に自動的にモデルアドレスが入力されます。それをコピーして`あなたの好きな英語のキャラクター名.yaml`に名前を変更します。
   - `yaml`ファイルと同じディレクトリに、後で使用する参照オーディオを配置し、`あなたの好きな英語のキャラクター名_参照オーディオのテキスト内容.wav`または`.mp3`と名前を付けます。例えば、`Huanyuv2_こんにちは、これはテストオーディオです.wav`です。
   - VideoLingoウェブページのサイドバーで、`GPT-SoVITSキャラクター`を`あなたの好きな英語のキャラクター名`に設定します。

   b. 事前トレーニングされたモデルを使用：
   - [ここ](https://vip.123pan.cn/1817874751/8137723)から私のモデルをダウンロードし、解凍して`GPT-SoVITS-v2-xxx`に上書きします。
   - `GPT-SoVITSキャラクター`を`Huanyuv2`に設定します。

   c. 他のトレーニング済みモデルを使用：
   - `xxx.ckpt`モデルファイルを`GPT_weights_v2`フォルダに配置し、`xxx.pth`モデルファイルを`SoVITS_weights_v2`フォルダに配置します。
   - 方法aを参照して、`tts_infer.yaml`ファイルの名前を変更し、ファイルの`custom`セクションの`t2s_weights_path`と`vits_weights_path`をあなたのモデルに指すように変更します。例えば：
  
      ```yaml
      # 方法bの設定例：
      t2s_weights_path: GPT_weights_v2/Huanyu_v2-e10.ckpt
      version: v2
      vits_weights_path: SoVITS_weights_v2/Huanyu_v2_e10_s150.pth
      ```
   - 方法aを参照して、`yaml`ファイルと同じディレクトリに、後で使用する参照オーディオを配置し、`あなたの好きな英語のキャラクター名_参照オーディオのテキスト内容.wav`または`.mp3`と名前を付けます。例えば、`Huanyuv2_こんにちは、これはテストオーディオです.wav`です。プログラムは自動的に認識して使用します。
   - ⚠️ 警告：**`キャラクター名`を英語で命名してください**。そうしないとエラーが発生します。`参照オーディオのテキスト内容`は中国語でもかまいません。現在はベータ版であり、エラーが発生する可能性があります。


   ```
   # 期待されるディレクトリ構造：
   .
   ├── VideoLingo
   │   └── ...
   └── GPT-SoVITS-v2-xxx
       ├── GPT_SoVITS
       │   └── configs
       │       ├── tts_infer.yaml
       │       ├── あなたの好きな英語のキャラクター名.yaml
       │       └── あなたの好きな英語のキャラクター名_参照オーディオのテキスト内容.wav
       ├── GPT_weights_v2
       │   └── [あなたのGPTモデルファイル]
       └── SoVITS_weights_v2
           └── [あなたのSoVITSモデルファイル]
   ```
        
構成が完了したら、ウェブページのサイドバーで`参照オーディオモード`を選択してください。VideoLingoは吹き替えステップ中にポップアップコマンドラインでGPT-SoVITSの推論APIポートを自動的に開きます。吹き替えが完了したら手動で閉じることができます。この方法はまだ非常に安定しておらず、単語や文が欠落する可能性や他のバグが発生する可能性があるため、注意して使用してください。</details>

## 🛠️ ソースコードのインストール手順

### Windowsの前提条件

VideoLingoのインストールを開始する前に、**20G**の空きディスクスペースがあることを確認し、以下の手順を完了してください：

| 依存関係 | whisperX 🖥️ | whisperX ☁️ |
|:-----|:-------------------|:----------------|
| Anaconda 🐍 | [ダウンロード](https://www.anaconda.com/products/distribution#download-section) | [ダウンロード](https://www.anaconda.com/products/distribution#download-section) |
| Git 🌿 | [ダウンロード](https://git-scm.com/download/win) | [ダウンロード](https://git-scm.com/download/win) |
| Cuda Toolkit 12.6 🚀 | [ダウンロード](https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe) | - |
| Cudnn 9.3.0 🧠 | [ダウンロード](https://developer.download.nvidia.com/compute/cudnn/9.3.0/local_installers/cudnn_9.3.0_windows.exe) | - |

> 注意：Anacondaをインストールする際に「システムパスに追加」をチェックし、インストール後にコンピュータを再起動してください🔄

### インストール手順

ある程度のPythonの知識が必要です。Win、Mac、Linuxをサポートしています。問題が発生した場合は、公式サイト[videolingo.io](https://videolingo.io)の右下のAIアシスタントに質問できます。

1. Anaconda Promptを開き、デスクトップディレクトリに切り替えます：
   ```bash
   cd desktop
   ```

2. プロジェクトをクローンし、プロジェクトディレクトリに切り替えます：
   ```bash
   git clone https://github.com/Huanshere/VideoLingo.git
   cd VideoLingo
   ```

3. 仮想環境を作成してアクティブ化します（**3.10.0である必要があります**）：
   ```bash
   conda create -n videolingo python=3.10.0 -y
   conda activate videolingo
   ```

4. インストールスクリプトを実行します：
   ```bash
   python install.py
   ```
   プロンプトに従って必要なwhisper方法を選択し、スクリプトは対応するtorchとwhisperバージョンを自動的にインストールします

5. **中国語の転写を使用する必要があるユーザーのみ**：
   
   Belle-whisper-large-v3-zh-punctモデルを手動でダウンロードし（[Baiduリンク](https://pan.baidu.com/s/1NyNtkEM0EMsjdCovncsx0w?pwd=938n)）、プロジェクトルートディレクトリの`_model_cache`フォルダに上書きし、ウェブページのサイドバーで**転写言語をzhに指定**してください

6. 🎉 コマンドを入力するか、`一键启动.bat`をクリックしてStreamlitアプリケーションを起動します：
   ```bash
   streamlit run st.py
   ```

7. ポップアップしたウェブページのサイドバーでキーを設定し、whisper方法を選択してください

   ![attention](https://github.com/user-attachments/assets/7db25130-d421-452e-a16a-d7cfb0478ebf)


8. （オプション）`config.py`で手動で詳細設定を行うことができます

<!-- 本プロジェクトは構造化モジュール開発を採用しており、`core\step__.py`ファイルを順番に実行できます。技術文書：[中文](./docs/README_guide_zh.md) ｜ [英文](./docs/README_guide_en.md)（更新予定） -->

## ⚠️ 注意事項

1. UVR5はシステムリソースの要求が高く、処理速度が遅いです。この機能を使用する場合は、16GB以上のメモリと8GB以上のVRAMを持つデバイスでのみ選択することをお勧めします。
   
2. 翻訳ステップで非常に低い確率で'phrase'エラーが発生する可能性があります。発生した場合はフィードバックをお願いします。
   
3. 吹き替え機能の品質は不安定です。最高の品質を得るためには、元のビデオに適したTTS速度を選択することをお勧めします。例えば、OAITTSの速度は比較的速く、FishTTSの速度はサンプルを聞いてから選択してください。

## 📄 ライセンス

本プロジェクトはApache 2.0ライセンスの下でライセンスされています。本プロジェクトを使用する際には、以下の規定に従ってください：

1. 作品を発表する際には、**VideoLingoによって生成された字幕であることを示すことを推奨します（強制ではありません）**。
2. 使用する大規模言語モデルとTTSの条約に従って注釈を付けてください。
3. コードをコピーする場合は、Apache 2.0ライセンスの完全なコピーを含めてください。

以下のオープンソースプロジェクトの貢献に心から感謝します。これらはVideoLingoの開発に重要なサポートを提供しました：

- [whisperX](https://github.com/m-bain/whisperX)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [json_repair](https://github.com/mangiucugna/json_repair)
- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)
- [BELLE](https://github.com/LianjiaTech/BELLE)

## 📬 お問い合わせ

- QQグループに参加：875297969
- GitHubで[Issues](https://github.com/Huanshere/VideoLingo/issues)または[Pull Requests](https://github.com/Huanshere/VideoLingo/pulls)を提出
- 私のTwitterをフォロー：[@Huanshere](https://twitter.com/Huanshere)
- 公式サイトを訪問：[videolingo.io](https://videolingo.io)

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo&Timeline)

---

<p align="center">VideoLingoが役に立ったと思ったら、ぜひ⭐️をお願いします！</p>
