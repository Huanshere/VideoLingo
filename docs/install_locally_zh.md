# 🏠 VideoLingo 本地部署指南 (Windows)

VideoLingo 提供多种 Whisper 方案的选择（因为目前为止没有唯一完美的选择）：

| 方案 | 优势 | 劣势 |
|:-----|:-----|:-----|
| **whisper_timestamped** | • 本地运行<br>• 安装简便<br>• 使用原生 Whisper 模型 | • 仅英文效果理想<br>• 需要8G以上显存的显卡 |
| **whisperX** (🌟推荐) | • 本地运行<br>• 基于 faster-whisper，性能卓越<br>• 多语言支持好 | • 需安装 CUDA 和 cuDNN<br>• 各语言需单独下载 wav2vec 模型<br>• 需要8G以上显存的显卡 |
| **whisperX_api** | • 利用 Replicate API，无需本地算力 | • Replicate 服务可能不稳定 偶发 CUDA 错误 |

## 📋 前期准备

1. 在 [云雾 API](https://api.wlai.vip/register?aff=TXMB) 注册账号并充值以获取令牌（或者换任意的claude-3.5-sonnet提供商）
   
   ![云雾 API 注册流程](https://github.com/user-attachments/assets/762520c6-1283-4ba9-8676-16869fb94700)

2. 若选用 `whisperX_api`，请注册 Replicate 账号并绑定支付方式，获取你的令牌

## 🛠️ 安装流程

### 前置依赖

在开始安装 VideoLingo 之前，请确保完成以下步骤：

1. 安装 [Visual Studio 2022](https://visualstudio.microsoft.com/zh-hans/thank-you-downloading-visual-studio/?sku=Community&channel=Release&version=VS2022&source=VSLandingPage&cid=2030&passive=false)
   - 选择并安装"使用 C++ 的桌面开发"组件包

2. 安装 [CMake](https://github.com/Kitware/CMake/releases/download/v3.30.2/cmake-3.30.2-windows-x86_64.msi)

3. 安装 [Anaconda](https://www.anaconda.com/download/success)

4. 安装 [Git](https://git-scm.com/download/win)

5. 对于选择 `whisperX` 的用户：
   - 安装 [Cuda Toolkit](https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe)
   - 安装 [Cudnn](https://developer.download.nvidia.com/compute/cudnn/9.3.0/local_installers/cudnn_9.3.0_windows.exe)
   - 完成安装后重启计算机

### 安装步骤

1. 克隆项目：
   ```bash
   git clone https://github.com/Huanshere/VideoLingo.git
   cd VideoLingo
   ```

2. 配置虚拟环境：
   ```bash
   conda create -n videolingo python=3.12.0
   conda activate videolingo
   ```

3. 运行安装脚本：
   ```bash
   python install.py
   ```
   根据提示选择所需的 Whisper 项目，脚本将自动安装相应的 torch 和 whisper 版本。

4. 🎉 启动 Streamlit 应用：
   ```bash
   streamlit run st.py
   ```
   在浏览器中打开 Web 界面，通过侧边栏选择相应的 Whisper 方法并进行配置。