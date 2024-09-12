# 🏠 VideoLingo 本地部署指南

VideoLingo 语音识别文本步骤提供多种 Whisper 方案的选择（因为目前为止没有唯一完美的选择），根据个人配置和需求选择一个即可。

| 方案 | 优势 | 劣势 |
|:-----|:-----|:-----|
| **whisper_timestamped** | • 本地运行<br>• 安装简便<br>• 使用原生 Whisper 模型 | • 仅英文效果理想<br>• 需要8G以上显存的显卡 |
| **whisperX**  | • 本地运行<br>• 基于 faster-whisper，性能卓越<br>• 多语言支持好 | • 需安装 CUDA 和 cuDNN<br>• 各语言需单独下载 wav2vec 模型<br>• 需要8G以上显存的显卡 |
| **whisperX_api** (🌟推荐) | • 利用 Replicate API，无需本地算力 | • Replicate 服务可能不稳定 偶发 CUDA 错误<br>• 使用的large-v3 标点效果可能不如v2 |

## 📋 前期准备

1. 获取 `claude-3-5-sonnet` 的 `API_KEY`，推荐便宜渠道：[云雾API](https://api2.wlai.vip/register?aff=TXMB)，仅仅 ￥35/1M，官方价格的 1/3。当然这一步你也可以换成别的api提供商，但仅仅建议选用 `claude-3-5-sonnet` > `Qwen 1.5 72B Chat` > `deepseek-coder`
 
   ![yunwu](https://github.com/user-attachments/assets/7aabfa87-06b5-4004-8d9e-fa4a0743a912)

2. 若选用 `whisperX_api`，请在 [Replicate官网](https://replicate.com/account/api-tokens) 注册并绑定支付方式，获取你的令牌。也可在 QQ 群联系我免费提供测试用。

## 💾 一键包下载

如果你不想手动安装,我们也提供了 `whisperX_api` 版本的 Windows 一键整合包:

1. 下载 `v0.6.1` 一键整合包(600M): [直达链接](https://vip.123pan.cn/1817874751/7989695) | [度盘备用](https://pan.baidu.com/s/1H_3PthZ3R3NsjS0vrymimg?pwd=ra64)

2. 解压下载的压缩文件到想要的位置

3. 双击运行解压后文件夹中的 `一键启动.bat`

4. 在打开的浏览器窗口中,按照界面提示进行配置和使用

> 提示: 网页中配置 key 的过程参考最下方图片

## 🛠️ 手动安装流程 (Windows)

### 前置依赖

在开始安装 VideoLingo 之前，注意预留至少 **20G** 硬盘空间，并请确保完成以下步骤：

1. 安装 [Anaconda](https://www.anaconda.com/download/success)
   - 一定要在安装过程中勾选 添加到环境变量

2. 安装 [Git](https://git-scm.com/download/win)

3. 对于选择 `whisperX` 的用户：
   - 安装 [Cuda Toolkit](https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe)
   - 安装 [Cudnn](https://developer.download.nvidia.com/compute/cudnn/9.3.0/local_installers/cudnn_9.3.0_windows.exe)
   - 完成安装后重启计算机
   > tips: 如果在后续运行中报错 CUDA Memory, 请自行在 ``core/all_whisper_methods/whisperX.py` 中调小 batch size 重试
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
   根据提示选择所需的 Whisper 项目，脚本将自动安装相应的 torch 和 whisper 版本

   请确保网络连接，并检查安装过程是否有报错

5. 🎉 启动 Streamlit 应用：
   ```bash
   streamlit run st.py
   ```

6. 在弹出网页的侧边栏中设置key，并注意选择whisper方法

   ![2](https://github.com/user-attachments/assets/ba5621f0-8320-4a45-8da8-9ea574b5c7cc)


## Docker一键部署

拉取镜像：

```bash
docker pull sguann/videolingo_app:latest
```

运行镜像：
```bash
docker run -d -p 8501:8501 -e API_KEY=xxx -e BASE_URL=xxx -e WHISPER_METHOD=xxx -e DISPLAY_LANGUAGE=xxx sguann/videolingo_app:latest
```

其中:

 - `API_KEY` 访问token,需要自行申请,推荐[云雾API](https://api2.wlai.vip/register?aff=TXMB)
 - `BASE_URL` API提供商接口，不需要v1后缀
 - `WHISPER_METHOD` Whisper模型，可选项分别为：`whisper_timestamped`、`whisperX`、`whisperX_api`, 默认`whisperX_api`
 - `DISPLAY_LANGUAGE` 显示语言，可选`zh_CN`, `zh_TW`, `en_US`, `ja_JP`, 默认`auto`
