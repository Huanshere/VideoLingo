# 🚀 开始使用

## 📋 API 准备
本项目需使用大语言模型、WhisperX 和 TTS ，每个环节都提供了多种选择，**请仔细阅读配置指南😊**
### 1. **获取大模型的 API_KEY**：

| 推荐模型 | 推荐提供商 | base_url | 价格 | 效果 |
|:-----|:---------|:---------|:-----|:---------|
| claude-3-5-sonnet-20240620 （默认） | [云雾 api](https://yunwu.zeabur.app/register?aff=TXMB) | https://yunwu.zeabur.app | ￥15 / 1M tokens（官网1/10） | 🤩 |

⚠️ 警告：prompt 涉及多步思维链和复杂的json格式，除了 claude 3.5 sonnet 模型，其他模型均容易出错。一小时视频花费约 ￥7。

> 注：云雾api 还支持 openai 的 tts-1 接口，可在配音步骤选用。

<details>
<summary>云雾api 如何获取 api key？</summary>

1. 点击上面 推荐提供商 的链接
2. 注册账户并充值
3. 在 api key 页面新建一个即可
4. 云雾api要注意勾选 `无限额度` ，模型处选择 `claude-3-5-sonnet-20240620` 模型，渠道建议选 `纯AZ 1.5倍`，如需配音时使用 `openai`，还需要勾选 `tts-1` 模型
</details>

<details>
<summary>能用别的模型吗？</summary>

- ✅ 支持 OAI-Like 的 API 接口，需要自行在 streamlit 侧边栏更换。
- ⚠️ 但其他模型（尤其是小模型）遵循指令要求能力弱，非常容易在翻译过程报错，强烈不推荐。
</details>

### 2. **准备 Replicate 的 Token** （仅当选用 whisperXapi ☁️ 时）

VideoLingo 使用 WhisperX 进行语音识别，支持本地部署和云端api。如果你没有显卡或者仅想快速体验，可以使用云端api及一键简易包。

#### 两者对比：
| 方案 | 缺点 |
|:-----|:-----|
| **whisperX 🖥️** | • 安装CUDA 🛠️<br>• 需下载模型 📥<br>• 高显存 💾 |
| **whisperXapi ☁️** | • 需梯子 🕵️‍♂️<br>• Visa卡 💳<br>• **中文效果差** 🚫 |

<details>
<summary>如何获取令牌</summary>
在 [Replicate](https://replicate.com/account/api-tokens) 注册并绑定 Visa 卡支付方式，获取令牌。**或加入 QQ 群在群公告中免费获取测试令牌**
</details>


### 3. **TTS 的 API**
VideoLingo提供了多种tts接入方式，以下是对比（如不使用配音仅翻译请跳过）

| TTS 方案 | 优点 | 缺点 | 中文效果 | 非中文效果 |
|:---------|:-----|:-----|:---------|:-----------|
| 🎙️ OpenAI TTS | 情感真实 | 中文听起来像外国人 | 😕 | 🤩 |
| 🔊 Azure TTS (推荐)  | 效果自然 | 充值不方便 | 🤩 | 😃 |
| 🎤 Fish TTS  | 真是本地人 | 官方模型有限 | 😂 | 😂 |
| 🗣️ GPT-SoVITS (测试) | 最强语音克隆 | 目前只支持中英文，需要N卡推理模型，配置需要相关知识 | 🏆 | 🚫 |

- OpenAI TTS，推荐使用 [云雾 api](https://yunwu.zeabur.app/register?aff=TXMB)，注意在模型处勾选 `tts-1`；
- **Azure TTS 可在QQ群公告获取测试 key** 或自行在 [官网](https://learn.microsoft.com/zh-cn/azure/ai-services/speech-service/get-started-text-to-speech?tabs=windows%2Cterminal&pivots=programming-language-python) 注册充值；
- Fish TTS 请自行在 [官网](https://fish.audio/zh-CN/go-api/) 注册（送10刀额度）

<details>
<summary>OpenAI 声音怎么选？</summary>

声音列表可以在 [官网](https://platform.openai.com/docs/guides/text-to-speech/voice-options) 找到，例如 `alloy`, `echo`, `nova`等，在 `config.yaml` 中修改 `openai_tts.voice` 即可。

</details>
<details>
<summary>Azure 声音怎么选？</summary>

建议在 [在线体验](https://speech.microsoft.com/portal/voicegallery) 中试听选择你想要的声音，在右边的代码中可以找到该声音对应的代号，例如 `zh-CN-XiaoxiaoMultilingualNeural`

</details>

<details>
<summary>Fish TTS 声音怎么选？</summary>

前往 [官网](https://fish.audio/zh-CN/) 中试听选择你想要的声音，在 URL 中可以找到该声音对应的代号，例如丁真是 `54a5170264694bfc8e9ad98df7bd89c3`，热门的几种声音已添加在 `config.yaml` 中。如需使用其他声音，请在 `config.yaml` 中修改 `fish_tts.character_id_dict` 字典。

</details>

<details>
<summary>GPT-SoVITS-v2 使用教程</summary>

1. 前往 [官方的语雀文档](https://www.yuque.com/baicaigongchang1145haoyuangong/ib3g1e/dkxgpiy9zb96hob4#KTvnO) 查看配置要求并下载整合包。

2. 将 `GPT-SoVITS-v2-xxx` 与 `VideoLingo` 放在同一个目录下。**注意是两文件夹并列。**

3. 选择以下任一方式配置模型：

   a. 自训练模型：
   - 训练好模型后， `GPT-SoVITS-v2-xxx\GPT_SoVITS\configs` 下的 `tts_infer.yaml` 已自动填写好你的模型地址，将其复制并重命名为 `你喜欢的英文角色名.yaml`
   - 在和 `yaml` 文件同个目录下，放入后续使用的参考音频，命名为 `你喜欢的英文角色名_参考音频的文字内容.wav` 或 `.mp3`，例如 `Huanyuv2_你好，这是一条测试音频.wav`
   - 在 VideoLingo 网页的侧边栏中，将 `GPT-SoVITS 角色` 配置为 `你喜欢的英文角色名`。

   b. 使用预训练模型：
   - 从 [这里](https://vip.123pan.cn/1817874751/8137723) 下载我的模型，解压后覆盖到 `GPT-SoVITS-v2-xxx`。
   - 在 `GPT-SoVITS 角色` 配置为 `Huanyuv2`。

   c. 使用其他训练好的模型：
   - 将 `xxx.ckpt` 模型文件放在 `GPT_weights_v2` 文件夹下，将 `xxx.pth` 模型文件放在 `SoVITS_weights_v2` 文件夹下。
   - 参考方法 a，重命名 `tts_infer.yaml` 文件，并修改文件中的 `custom` 部分的 `t2s_weights_path` 和 `vits_weights_path` 指向你的模型，例如：
  
      ```yaml
      # 示例 法 b 的配置：
      t2s_weights_path: GPT_weights_v2/Huanyu_v2-e10.ckpt
      version: v2
      vits_weights_path: SoVITS_weights_v2/Huanyu_v2_e10_s150.pth
      ```
   - 参考方法 a，在和 `yaml` 文件同个目录下，放入后续使用的参考音频，命名为 `你喜欢的英文角色名_参考音频的文字内容.wav` 或 `.mp3`，例如 `Huanyuv2_你好，这是一条测试音频.wav`，程序会自动识别并使用。
   - ⚠️ 警告：**请使用英文命名 `角色名`** ，否则会出现错误。 `参考音频的文字内容` 可以使用中文。目前仍处于测试版，可能产生报错。


   ```
   # 期望的目录结构：
   .
   ├── VideoLingo
   │   └── ...
   └── GPT-SoVITS-v2-xxx
       ├── GPT_SoVITS
       │   └── configs
       │       ├── tts_infer.yaml
       │       ├── 你喜欢的英文角色名.yaml
       │       └── 你喜欢的英文角色名_参考音频的文字内容.wav
       ├── GPT_weights_v2
       │   └── [你的GPT模型文件]
       └── SoVITS_weights_v2
           └── [你的SoVITS模型文件]
   ```
        
配置完成后，注意在网页侧边栏选择 `参考音频模式`（具体原理可以参考语雀文档），VideoLingo 在配音步骤时会自动在弹出的命令行中打开 GPT-SoVITS 的推理 API 端口，配音完成后可手动关闭。注意，此方法的稳定性取决于选择的底模。</details>

## 💨 Win 一键简易包

### 注意事项：

**简易包并不具备从源码安装的完整功能**，仅供快速体验用（现在更推荐使用colab版本进行体验），如果需要处理长视频及完整功能，建议使用源码安装。以下是两者的对比：

| 简易包 | 源码安装 |
|------------|--------------|
| 💻 CPU 版本 torch，约 **2.7G** | 🖥️ 需 Nvidia 显卡和 **25G** 硬盘 |
| 🐢 UVR5 人声分离在 CPU 上较慢 | 🚀 GPU 加速 UVR5 |
| ☁️ 仅支持 whisperXapi，不支持本地 whisperX | 🏠 支持本地 whisperX |
| 🈚 不支持中文转录 | 🈶 支持中文转录 |
| 🎵 转录步骤未进行人声分离，不适用于 BGM 嘈杂视频 | 🎼 可处理 BGM 嘈杂视频 |

### 下载和使用说明

1. 下载 `v1.5` 一键简易包(800M): [直接下载](https://vip.123pan.cn/1817874751/8313069) | [度盘备用](https://pan.baidu.com/s/1H_3PthZ3R3NsjS0vrymimg?pwd=ra64)

2. 解压后双击运行文件夹中的 `一键启动.bat`

3. 在打开的浏览器窗口中，在侧边栏进行必要配置，然后一键出片！
  ![cn_cloud_set](https://github.com/user-attachments/assets/cb25318f-54ad-404e-a864-e46059415cf9)

## 🛠️ 源码安装流程

### Windows 前置依赖

在开始安装 VideoLingo 之前，注意预留 **25G** 硬盘空间，并根据是否使用本地运行的 whisper 模型安装列表中的依赖软件：

| 依赖 | whisperX 🖥️ | whisperX ☁️ |
|:-----|:-------------------|:----------------|
| Anaconda 🐍 | [下载](https://www.anaconda.com/products/distribution#download-section) | [下载](https://www.anaconda.com/products/distribution#download-section) |
| Git 🌿 | [下载](https://git-scm.com/download/win) | [下载](https://git-scm.com/download/win) |
| Cuda Toolkit 12.6 🚀 | [下载](https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe) | - |
| Cudnn 9.3.0 🧠 | [下载](https://developer.download.nvidia.com/compute/cudnn/9.3.0/local_installers/cudnn_9.3.0_windows.exe) | - |

> 注意：安装 Anaconda 时勾选 `添加到系统Path`，安装完 Cuda 和 Cudnn 后需要重启计算机 🔄

### 安装步骤

需要一定的 python 基础，支持Win, Mac, Linux。遇到任何问题可以询问官方网站 [videolingo.io](https://videolingo.io) 右下角的AI助手~

1. 打开 Anaconda Prompt 并切换到桌面目录：
   ```bash
   cd desktop
   ```

2. 克隆项目并切换至项目目录：
   ```bash
   git clone https://github.com/Huanshere/VideoLingo.git
   cd VideoLingo
   ```

3. 创建并激活虚拟环境（**必须 3.10.0**）：
   ```bash
   conda create -n videolingo python=3.10.0 -y
   conda activate videolingo
   ```

4. 运行安装脚本：
   ```bash
   python install.py
   ```
   根据提示选择所需的 whisper 方法，脚本将自动安装相应的 torch 和 whisper 版本

5. 仅**对于需要使用中文转录**的用户：
   
   请手动下载 Belle-whisper-large-v3-zh-punct 模型（[度盘链接](https://pan.baidu.com/s/1NyNtkEM0EMsjdCovncsx0w?pwd=938n)），并将其覆盖在项目根目录的 `_model_cache` 文件夹下，并注意在网页侧边栏指定**转录语言为zh**

6. 🎉 输入命令或点击 `一键启动.bat` 启动 Streamlit 应用：
   ```bash
   streamlit run st.py
   ```

7. 在弹出网页的侧边栏中设置key，并注意选择whisper方法

   ![zh_set](https://github.com/user-attachments/assets/bb9381d0-8d99-4d8b-aaff-9846076fc7a3)


9. （可选）更多进阶设置可以在 `config.yaml` 中手动修改，运行过程请注意命令行输出

## 🚨 常见报错

1. **'Empty Translation Line'**: 这是由于选用了较笨的LLM，在翻译时把一些短语句直接省略了。解决方案：请换用Claude 3.5 Sonnet重试。

2. **翻译过程的 'Key Error'**: 
   - 原因1：同上，弱模型遵循JSON格式能力有误。
   - 原因2：对于敏感内容，LLM可能拒绝翻译。
   解决方案：请检查 `output/gpt_log/error.json` 的 `response` 和 `msg` 字段。

3. **'Retry Failed', 'SSL', 'Connection', 'Timeout'**: 通常是网络问题。解决方案：中国大陆用户请切换网络节点重试。