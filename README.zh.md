<div align="center">

<img src="docs/logo.png" alt="VideoLingo Logo" height="140">

# VideoLingo: 连接世界的每一帧
<p align="center">
  <a href="https://www.python.org" target="_blank"><img src="https://img.shields.io/badge/Python-3.10-blue.svg" alt="Python"></a>
  <a href="https://github.com/Huanshere/VideoLingo/blob/main/LICENSE" target="_blank"><img src="https://img.shields.io/github/license/Huanshere/VideoLingo.svg" alt="License"></a>
  <a href="https://github.com/Huanshere/VideoLingo/stargazers" target="_blank"><img src="https://img.shields.io/github/stars/Huanshere/VideoLingo.svg" alt="GitHub stars"></a>
  <a href="https://colab.research.google.com/github/Huanshere/VideoLingo/blob/main/VideoLingo_colab.ipynb" target="_blank"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a>
</p>

[**English**](README.md)｜[**中文**](README.zh.md) | [**日本語**](README.ja.md)

**QQ群：875297969**

</div>

## 🌟 项目简介

VideoLingo 是一站式视频翻译本地化配音工具，旨在生成 Netflix 级别的高质量字幕，告别生硬机翻，告别多行字幕，还能加上高质量的配音，让全世界的知识能够跨越语言的障碍共享。通过直观的 Streamlit 网页界面，只需点击两下就能完成从视频链接到内嵌高质量双语字幕甚至带上配音的整个流程，轻松创建 Netflix 品质的本地化视频。

主要特点和功能：
- 🎥 使用 yt-dlp 从 Youtube 链接下载视频

- 🎙️ 使用 WhisperX 进行单词级时间轴字幕识别

- **📝 使用 NLP 和 GPT 根据句意进行字幕分割**

- **📚 GPT 总结提取术语知识库，上下文连贯翻译**

- **🔄 三步直译、反思、意译，媲美字幕组精翻效果**

- **✅ 按照 Netflix 标准检查单行长度，绝无双行字幕**

- **🗣️ 使用 GPT-SoVITS 等方法对齐配音**

- 🚀 整合包一键启动，在 streamlit 中一键出片

- 📝 详细记录每步操作日志，支持随时中断和恢复进度

- 🌐 全面的多语言支持，轻松实现跨语言视频本地化

与同类项目的主要区别：**绝无多行字幕，最佳的翻译质量**

## 🎥 效果演示

<table>
<tr>
<td width="33%">

### 俄语翻译
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

### 语言支持：

当前输入语言支持和示例：

| 输入语言 | 支持程度 | 翻译demo |
|---------|---------|---------|
| 英语 | 🤩 | [英转中](https://github.com/user-attachments/assets/127373bb-c152-4b7a-8d9d-e586b2c62b4b) |
| 俄语 | 😊 | [俄转中](https://github.com/user-attachments/assets/25264b5b-6931-4d39-948c-5a1e4ce42fa7) |
| 法语 | 🤩 | [法转日](https://github.com/user-attachments/assets/3ce068c7-9854-4c72-ae77-f2484c7c6630) |
| 德语 | 🤩 | [德转中](https://github.com/user-attachments/assets/07cb9d21-069e-4725-871d-c4d9701287a3) |
| 意大利语 | 🤩 | [意转中](https://github.com/user-attachments/assets/f1f893eb-dad3-4460-aaf6-10cac999195e) |
| 西班牙语 | 🤩 | [西转中](https://github.com/user-attachments/assets/c1d28f1c-83d2-4f13-a1a1-859bd6cc3553) |
| 日语 | 😐 | [日转中](https://github.com/user-attachments/assets/856c3398-2da3-4e25-9c36-27ca2d1f68c2) |
| 中文* | 🤩 | [中转英](https://github.com/user-attachments/assets/48f746fe-96ff-47fd-bd23-59e9202b495c) |
> *中文需单独配置whisperX模型，详见源码安装，并注意在网页侧边栏指定转录语言为zh

翻译语言支持大模型会的所有语言，配音语言取决于选取的TTS方法。

## 🚀 Win 一键整合包

### 注意事项：

- 整合包使用 CPU 版本 torch，约 **2.6G**。
- UVR5 人声分离在 CPU 上较慢。
- 仅支持 whisperXapi ☁️，不支持本地 whisperX 💻。
- 不支持中文转录。
- 转录步骤未进行人声分离，不适用于 BGM 嘈杂视频。

需要以下功能请从源码安装（需 Nvidia 显卡和 **20G** 硬盘）：
- 中文转录
- 本地 whisperX 💻
- GPU 加速 UVR5
- 处理 BGM 嘈杂视频

### 下载和使用说明

1. 下载 `v1.4` 一键整合包(800M): [直接下载](https://vip.123pan.cn/1817874751/8209290) | [度盘备用](https://pan.baidu.com/s/1H_3PthZ3R3NsjS0vrymimg?pwd=ra64)

2. 解压后双击运行文件夹中的 `一键启动.bat`

3. 在打开的浏览器窗口中，在侧边栏进行必要配置，然后一键出片！
  ![attention](https://github.com/user-attachments/assets/7db25130-d421-452e-a16a-d7cfb0478ebf)


> 💡 提示: 本项目需要配置大模型, WhisperX, TTS，请仔细往下阅读 **API 准备**

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

VideoLingo 使用 WhisperX 进行语音识别，支持本地部署和云端api。如果你没有显卡或者仅想快速体验，可以使用云端api。

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

声音列表可以在 [官网](https://platform.openai.com/docs/guides/text-to-speech/voice-options) 找到，例如 `alloy`, `echo`, `nova`等，在 `config.py` 中修改 `OAI_VOICE` 即可。

</details>
<details>
<summary>Azure 声音怎么选？</summary>

建议在 [在线体验](https://speech.microsoft.com/portal/voicegallery) 中试听选择你想要的声音，在右边的代码中可以找到该声音对应的代号，例如 `zh-CN-XiaoxiaoMultilingualNeural`

</details>

<details>
<summary>Fish TTS 声音怎么选？</summary>

前往 [官网](https://fish.audio/zh-CN/) 中试听选择你想要的声音，在 URL 中可以找到该声音对应的代号，例如丁真是 `54a5170264694bfc8e9ad98df7bd89c3`，热门的几种声音已添加在 `config.py` 中，直接修改 `FISH_TTS_CHARACTER` 即可。如需使用其他声音，请在 `config.py` 中修改 `FISH_TTS_CHARACTER_ID_DICT` 字典。

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

## 🛠️ 源码安装流程

### Windows 前置依赖

在开始安装 VideoLingo 之前，注意预留 **20G** 硬盘空间，并请确保完成以下步骤：

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

   ![attention](https://github.com/user-attachments/assets/7db25130-d421-452e-a16a-d7cfb0478ebf)


8. （可选）更多进阶设置可以在 `config.py` 中手动修改，运行过程请注意命令行输出

<!-- 本项目采用结构化模块开发，可按顺序逐个运行 `core\step__.py`，技术文档: [中文](./docs/README_guide_zh.md) ｜ [英文](./docs/README_guide_en.md)（待更新） -->

## ⚠️ 当前限制

1. **UVR5 人声分离对系统资源要求较高**，处理速度较慢。建议仅在拥有 16GB 以上内存和 8GB 以上显存的设备上勾选使用此功能。注意：对于BGM过吵的视频，如果不在 whisper 前进行人声分离，很可能会导致单词级字幕黏连，在最后的对齐步骤抛出错误。

   
2. **配音功能的质量可能不完美**，归根结底是因为语言结构差异、以及源语言与目标语言之间的语素信息密度不同。为获得最佳效果，建议根据原视频的语速和内容特点，选择相近语速的 TTS。最佳实践是使用GPT-SoVITS训练原视频声音，然后采取 `模式3:使用每一条参考音频` 进行配音，这样能最大程度保证音色、语速、语气的吻合，效果见 [demo](https://www.bilibili.com/video/BV1mt1QYyERR/?share_source=copy_web&vd_source=fa92558c28cd668d33dabaddb17e2f9e)。

3. **多语言视频转录识别仅仅只会保留主要语言**，这是由于 whisperX 在强制对齐单词级字幕时使用的是针对单个语言的特化模型，会因为不认识另一种语言而删去。

3. **多角色分别配音暂不可用**，whisperX 具有 VAD 的潜力，但是具体需要一些施工，暂时没有开发此功能。

## 🚨 常见报错

1. **'Empty Translation Line'**: 这是由于选用了较笨的LLM，在翻译时把一些短语句直接省略了。解决方案：请换用Claude 3.5 Sonnet重试。

2. **翻译过程的 'Key Error'**: 
   - 原因1：同上，弱模型遵循JSON格式能力有误。
   - 原因2：对于敏感内容，LLM可能拒绝翻译。
   解决方案：请检查 `output/gpt_log/error.json` 的 `response` 和 `msg` 字段。

3. **'Retry Failed', 'SSL', 'Connection', 'Timeout'**: 通常是网络问题。解决方案：中国大陆用户请切换网络节点重试。

## 📄 许可证

本项目采用 Apache 2.0 许可证。使用本项目时，请遵循以下规定：

1. 发表作品时**建议（不强制要求）标注字幕由 VideoLingo 生成**。
2. 遵循使用的大模型和TTS条约进行备注。
3. 如拷贝代码请包含完整的 Apache 2.0 许可证副本。

我们衷心感谢以下开源项目的贡献，它们为 VideoLingo 的开发提供了重要支持：

- [whisperX](https://github.com/m-bain/whisperX)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [json_repair](https://github.com/mangiucugna/json_repair)
- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)
- [BELLE](https://github.com/LianjiaTech/BELLE)

## 📬 联系我们

- 加入我们的 QQ 群：875297969
- 在 GitHub 上提交 [Issues](https://github.com/Huanshere/VideoLingo/issues) 或 [Pull Requests](https://github.com/Huanshere/VideoLingo/pulls)
- 关注我的 Twitter：[@Huanshere](https://twitter.com/Huanshere)
- 访问官方网站：[videolingo.io](https://videolingo.io)

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo&Timeline)

---

<p align="center">如果觉得 VideoLingo 有帮助，请给我们一个 ⭐️！</p>