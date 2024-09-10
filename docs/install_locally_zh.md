# 🏠 VideoLingo 本地部署指南 (Windows)

VideoLingo 语音识别文本步骤提供多种 Whisper 方案的选择（因为目前为止没有唯一完美的选择），根据个人配置和需求选择一个即可。

| 方案 | 优势 | 劣势 |
|:-----|:-----|:-----|
| **whisper_timestamped** | • 本地运行<br>• 安装简便<br>• 使用原生 Whisper 模型 | • 仅英文效果理想<br>• 需要8G以上显存的显卡 |
| **whisperX**  | • 本地运行<br>• 基于 faster-whisper，性能卓越<br>• 多语言支持好 | • 需安装 CUDA 和 cuDNN<br>• 各语言需单独下载 wav2vec 模型<br>• 需要8G以上显存的显卡 |
| **whisperX_api** (🌟推荐) | • 利用 Replicate API，无需本地算力 | • Replicate 服务可能不稳定 偶发 CUDA 错误<br>• 使用的large-v3 标点效果可能不如v2 |

## 📋 前期准备

1. 在 [云雾 API](https://api.wlai.vip/register?aff=TXMB) 注册账号并充值以获取令牌（或者换任意的claude-3.5-sonnet提供商）
   > 为了最佳效果请选择claude-3.5-sonnet, 若测试体验也可选择 deepseek-coder，稍后在侧边栏进行设置
   
   ![云雾 API 注册流程](https://github.com/user-attachments/assets/762520c6-1283-4ba9-8676-16869fb94700)

2. 若选用 `whisperX_api`，请注册 Replicate 账号并绑定支付方式，获取你的令牌。也可联系我，我可以免费提供给你key测试用。

## 💾 一键包下载

如果你不想手动安装,我们也提供了 `whisperX_api` 版本的一键安装包:

1. 下载 `v0.6.0` 一键安装包(600M): [直达链接](https://your-download-link-here.com) | [度盘备用](https://pan.baidu.com/s/16nV3ccnGCjASzYlLnMRP_Q?pwd=6969)

2. 解压下载的压缩文件到想要的位置

3. 双击运行解压后文件夹中的 `一键启动.bat`

4. 在打开的浏览器窗口中,按照界面提示进行配置和使用

> 注意:一键包中已包含所有必要的依赖,无需额外安装。但仍需要准备好API密钥才能使用全部功能,在网页中配置key的过程可参考最底下。

## 🛠️ 手动安装流程

### 前置依赖

在开始安装 VideoLingo 之前，注意预留至少 **20G** 硬盘空间，并请确保完成以下步骤：

1. 安装 [Anaconda](https://www.anaconda.com/download/success)
   - 一定要在安装过程中勾选 添加到环境变量

2. 安装 [Git](https://git-scm.com/download/win)

3. 对于选择 `whisperX` 的用户：
   - 安装 [Cuda Toolkit](https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe)
   - 安装 [Cudnn](https://developer.download.nvidia.com/compute/cudnn/9.3.0/local_installers/cudnn_9.3.0_windows.exe)
   - 完成安装后重启计算机

4. 对于选择 `whisper_timestamped` 的用户：
   - 安装 [Visual Studio 2022](https://visualstudio.microsoft.com/zh-hans/thank-you-downloading-visual-studio/?sku=Community&channel=Release&version=VS2022&source=VSLandingPage&cid=2030&passive=false)
     - 在安装界面勾选"使用 C++ 的桌面开发"组件包
   - 安装 [CMake](https://github.com/Kitware/CMake/releases/download/v3.30.2/cmake-3.30.2-windows-x86_64.msi)

### 安装步骤
> 遇到问题可以把整个步骤丢给 GPT 问问~
1. 打开 Anaconda Powershell Prompt 并切换到桌面目录：
   ```bash
   cd desktop
   ```

2. 克隆项目：
   ```bash
   git clone https://github.com/Huanshere/VideoLingo.git
   cd VideoLingo
   ```

3. 配置虚拟环境：
   ```bash
   conda create -n videolingo python=3.10.0
   conda activate videolingo
   ```

4. 运行安装脚本：
   ```bash
   python install.py
   ```
   根据提示选择所需的 Whisper 项目，脚本将自动安装相应的 torch 和 whisper 版本。

5. 🎉 启动 Streamlit 应用：双击 `一键启动.bat` 或输入
   ```bash
   streamlit run st.py
   ```
   在浏览器中打开 Web 界面，通过侧边栏选择相应的 Whisper 方法并进行配置。

6. 在弹出网页的侧边栏中设置key，并注意选择正确使用的whisper方法

   ![2](https://github.com/user-attachments/assets/ba5621f0-8320-4a45-8da8-9ea574b5c7cc)


