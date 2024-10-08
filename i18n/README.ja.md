<div align="center">

<img src="/docs/logo.png" alt="VideoLingo Logo" height="140">

# VideoLingo: 世界をつなぐ一コマ一コマ
<p align="center">
  <a href="https://www.python.org" target="_blank"><img src="https://img.shields.io/badge/Python-3.10-blue.svg" alt="Python"></a>
  <a href="https://github.com/Huanshere/VideoLingo/blob/main/LICENSE" target="_blank"><img src="https://img.shields.io/github/license/Huanshere/VideoLingo.svg" alt="License"></a>
  <a href="https://github.com/Huanshere/VideoLingo/stargazers" target="_blank"><img src="https://img.shields.io/github/stars/Huanshere/VideoLingo.svg" alt="GitHub stars"></a>
  <a href="https://colab.research.google.com/github/Huanshere/VideoLingo/blob/main/VideoLingo_colab.ipynb" target="_blank"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a>
</p>

[**English**](/README.md)｜[**中文**](/i18n/README.zh.md) | [**日本語**](/i18n/README.ja.md)

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
<td width="33%">

### ロシア語翻訳
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

### 言語サポート：

現在サポートされている入力言語と例：

| 入力言語 | サポートレベル | 翻訳デモ |
|---------|---------|---------|
| 英語 | 🤩 | [英語から中国語](https://github.com/user-attachments/assets/127373bb-c152-4b7a-8d9d-e586b2c62b4b) |
| ロシア語 | 😊 | [ロシア語から中国語](https://github.com/user-attachments/assets/25264b5b-6931-4d39-948c-5a1e4ce42fa7) |
| フランス語 | 🤩 | [フランス語から日本語](https://github.com/user-attachments/assets/3ce068c7-9854-4c72-ae77-f2484c7c6630) |
| ドイツ語 | 🤩 | [ドイツ語から中国語](https://github.com/user-attachments/assets/07cb9d21-069e-4725-871d-c4d9701287a3) |
| イタリア語 | 🤩 | [イタリア語から中国語](https://github.com/user-attachments/assets/f1f893eb-dad3-4460-aaf6-10cac999195e) |
| スペイン語 | 🤩 | [スペイン語から中国語](https://github.com/user-attachments/assets/c1d28f1c-83d2-4f13-a1a1-859bd6cc3553) |
| 日本語 | 😐 | [日本語から中国語](https://github.com/user-attachments/assets/856c3398-2da3-4e25-9c36-27ca2d1f68c2) |
| 中国語* | 🤩 | [中国語から英語](https://github.com/user-attachments/assets/48f746fe-96ff-47fd-bd23-59e9202b495c) |
> *中国語はwhisperXモデルの別途設定が必要です。詳細はソースコードのインストールを参照し、ウェブページのサイドバーで転写言語をzhに指定してください。

翻訳言語は大規模言語モデルが対応するすべての言語をサポートし、吹き替え言語は選択したTTS方法に依存します。

## 🚀 Windows用ワンクリック統合パッケージ

### 注意事項：

- 統合パッケージはCPUバージョンのtorchを使用しており、約**2.6G**です。
- UVR5音声分離はCPU上で遅くなります。
- whisperXapi ☁️のみをサポートし、ローカルのwhisperX 💻はサポートしていません。
- 中国語の転写をサポートしていません。
- 転写ステップで音声分離を行っていないため、BGMが騒がしいビデオには適していません。

以下の機能が必要な場合は、ソースコードからインストールしてください（Nvidia GPUと**20G**のディスクスペースが必要）：
- 中国語の転写
- ローカルのwhisperX 💻
- GPU加速のUVR5
- BGMが騒がしいビデオの処理

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
| claude-3-5-sonnet-20240620（デフォルト） | [雲霧api](https://yunwu.zeabur.app/register?aff=TXMB) | https://yunwu.zeabur.app | ￥15 / 1M tokens（公式の1/10） | 🤩 |

⚠️ 警告：プロンプトには複数ステップの思考チェーンと複雑なJSON形式が含まれているため、Claude 3.5 Sonnetモデル以外のモデルではエラーが発生しやすくなっています。1時間のビデオの処理には約￥7かかります。

> 注：雲霧apiはopenaiのtts-1インターフェースもサポートしており、吹き替えステップで使用できます。

<details>
<summary>雲霧apiでAPIキーを取得する方法は？</summary>

1. 上記の推奨プロバイダーのリンクをクリック
2. アカウントを登録し、チャージ
3. APIキーのページで新しいキーを作成
4. 雲霧apiの場合、`無制限のクォータ`をチェックし、`claude-3-5-sonnet-20240620`モデルを選択し、`純AZ 1.5倍`チャネルを選択することをお勧めします。吹き替えにopenaiを使用する場合は、`tts-1`モデルもチェックしてください。
</details>

<details>
<summary>他のモデルを使用できますか？</summary>

- ✅ OAI-Like APIインターフェースをサポートしていますが、Streamlitのサイドバーで自分で変更する必要があります。
- ⚠️ ただし、他のモデル（特に小さなモデル）は指示に従う能力が弱く、翻訳中にエラーが発生する可能性が非常に高いため、強くお勧めしません。
</details>

### 2. **Replicateのトークンを準備**（whisperXapi ☁️を使用する場合のみ）

VideoLingoはWhisperXを使用して音声認識を行い、ローカルデプロイメントとクラウドAPIの両方をサポートしています。GPUがない場合や、すぐに体験したい場合は、クラウドAPIを使用できます。

#### オプションの比較：
| オプション | 欠点 |
|:-----|:-----|
| **whisperX 🖥️** | • CUDAのインストール 🛠️<br>• モデルのダウンロード 📥<br>• 高いVRAM要件 💾 |
| **whisperXapi ☁️** | • VPNが必要 🕵️‍♂️<br>• Visaカード 💳<br>• **中国語の効果が悪い** 🚫 |

<details>
<summary>トークンの取得方法</summary>
[Replicate](https://replicate.com/account/api-tokens)に登録し、Visaカードの支払い方法をバインドしてトークンを取得します。**またはQQグループに参加し、グループのアナウンスから無料のテストトークンを取得できます**
</details>

### 3. **TTSのAPI**
VideoLingoは複数のTTS統合方法を提供しています。以下は比較です（吹き替えを使用せず、翻訳のみの場合はスキップしてください）：

| TTSオプション | 利点 | 欠点 | 中国語の効果 | 非中国語の効果 |
|:---------|:-----|:-----|:---------|:-----------|
| 🎙️ OpenAI TTS | 感情がリアル | 中国語は外国人のように聞こえる | 😕 | 🤩 |
| 🔊 Azure TTS (推奨)  | 自然な効果 | チャージが不便 | 🤩 | 😃 |
| 🎤 Fish TTS  | 本物のローカル話者のよう | 公式モデルが限られている | 😂 | 😂 |
| 🗣️ GPT-SoVITS (ベータ) | 最強の音声クローン | 現在中国語と英語のみをサポート、モデル推論にGPUが必要、設定に関連知識が必要 | 🏆 | 🚫 |

- OpenAI TTSの場合、[雲霧api](https://yunwu.zeabur.app/register?aff=TXMB)を使用することをお勧めします。`tts-1`モデルをチェックすることを忘れないでください。
- **Azure TTSの無料キーはQQグループのアナウンスで取得できます** または[公式サイト](https://learn.microsoft.com/zh-cn/azure/ai-services/speech-service/get-started-text-to-speech?tabs=windows%2Cterminal&pivots=programming-language-python)で自分で登録してチャージできます。
- Fish TTSは[公式サイト](https://fish.audio/zh-CN/go-api/)で自分で登録してください（10ドルの無料クレジットあり）

<details>
<summary>OpenAIの声を選ぶ方法は？</summary>

声のリストは[公式サイト](https://platform.openai.com/docs/guides/text-to-speech/voice-options)で見つけることができます。例えば、`alloy`、`echo`、`nova`などです。`config.py`で`OAI_VOICE`を変更して声を変更します。

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

## ⚠️ 現在の制限事項

1. **UVR5 音声分離はシステムリソースの要求が高く**、処理速度が遅いです。16GB以上のメモリと8GB以上のVRAMを持つデバイスでのみこの機能の使用をお勧めします。注意：BGMが大きすぎる動画の場合、whisper前に音声分離を行わないと、単語レベルの字幕が連結してしまい、最後の整列ステップでエラーが発生する可能性が高くなります。

2. **吹き替え機能の品質は完璧ではない可能性があります**。これは主に言語構造の違いや、ソース言語と目標言語の間の音素情報密度の違いが原因です。最良の結果を得るには、元の動画の話速と内容の特徴に基づいて、類似した話速のTTSを選択することをお勧めします。最適な方法は、GPT-SoVITSを使用して元の動画の音声をトレーニングし、その後「モード3：各参照音声を使用」で吹き替えを行うことです。これにより、音色、話速、イントネーションの一致度を最大限に保証できます。効果は[デモ](https://www.bilibili.com/video/BV1mt1QYyERR/?share_source=copy_web&vd_source=fa92558c28cd668d33dabaddb17e2f9e)をご覧ください。

3. **多言語動画の文字起こしでは主要言語のみが保持されます**。これはwhisperXが単語レベルの字幕を強制的に整列する際に、単一言語に特化したモデルを使用するため、他の言語を認識せずに削除してしまうためです。

4. **複数の役割ごとの個別の吹き替えは現在利用できません**。whisperXにはVADの潜在能力がありますが、具体的な実装にはいくつかの作業が必要で、現時点ではこの機能を開発していません。

## 🚨 よくあるエラー

1. **'Empty Translation Line'**: これは比較的能力の低いLLMを選択したことが原因で、翻訳時に一部の短い文を省略してしまったためです。解決策：Claude 3.5 Sonnetに切り替えて再試行してください。

2. **翻訳プロセスでの 'Key Error'**: 
   - 原因1：上記と同様に、弱いモデルがJSON形式に従う能力が不足しています。
   - 原因2：センシティブな内容に対して、LLMが翻訳を拒否する可能性があります。
   解決策：`output/gpt_log/error.json`の`response`と`msg`フィールドを確認してください。

3. **'Retry Failed', 'SSL', 'Connection', 'Timeout'**: 通常はネットワークの問題です。解決策：中国本土のユーザーはネットワークノードを切り替えて再試行してください。

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
