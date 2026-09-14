# Release notes since v3.0.1 / v3.0.1 之后的版本更新说明

## Maintainer handoff / 发布前说明

- **Status:** release-note proposal, not a published release. The maintainer chooses the next version and tag. Repository metadata currently says `3.0.3`; this document does not change version metadata or create a tag.
- **Scope:** [`v3.0.1`](https://github.com/Huanshere/VideoLingo/releases/tag/v3.0.1), published on 2026-02-28, through merged upstream commit [`dcf55ff`](https://github.com/Huanshere/VideoLingo/commit/dcf55ff078d3d3fdadcdfdbd2f790539cfbaaab9), checked on 2026-09-14. The range contains 17 commits, including merge commits, and ten non-merge commits.
- **Refresh before publishing:** #599, #601 and [#602](https://github.com/Huanshere/VideoLingo/pull/602) are all merged and included. Recheck commits after the cutoff before selecting the release target. Unmerged proposals are not part of these notes.
- **Publication:** review the notes and upgrade caveats, choose the release tag/target and any assets, then copy the English and Chinese sections below into a GitHub Release. Merging this documentation PR does not create or publish a release.
- **Editorial note:** describe the final source state rather than every intermediate implementation. In particular, `setup_env.py` now defaults to Python 3.13 even though some introductory README instructions still mention 3.10. Reconcile those instructions before publishing.

- **状态：**这是发布说明提案，尚未发布新版本。下一个版本号和标签由维护者决定。仓库版本元数据目前为 `3.0.3`，本文不会修改版本号或创建标签。
- **范围：**从 2026-02-28 发布的 `v3.0.1` 到已合并的上游提交 `dcf55ff`，核对日期为 2026-09-14。包含合并提交在内共 17 个提交，其中 10 个为非合并提交。
- **发布前更新：**#599、#601、#602 均已合并并计入下方说明。选定发布目标前应检查截止提交之后的新增改动；未合并提案不计入本说明。
- **发布方式：**审核说明和升级注意事项，确定标签、目标提交及附件后，将下方中英文正文复制到 GitHub Release。合并此文档 PR 不会自动创建或发布版本。
- **编辑注意：**本文描述最终代码状态，不把开发过程中的每次实现都当作独立功能。例如，`setup_env.py` 当前默认 Python 3.13，但部分 README 入门说明仍写 3.10，发布前需统一。

---

## English release notes

This update brings together the changes merged since v3.0.1: easier installation with local or shared environments, searchable model selection, background task controls, an audio-only subtitle workflow, broader interface localization, and fixes for downloads, subtitle timing and dubbing compatibility.

### Installation and startup

- Added a uv-based setup path without requiring Anaconda, with project-local `.venv`, shared `~/.venvs/videolingo`, or a custom environment path. New environments now default to **Python 3.13**. The Windows batch-processing launcher supports a project-local uv environment. (#537, #577, #599)
- Added the stage-based `installer.py` with installation-state tracking, requirements/version checks, retryable package installation, explicit force/upgrade options, and optional Demucs handling. `install.py` remains a compatibility entry point. (#577, #599)
- Consolidated Windows startup in `OneKeyStart.bat`: prefer the shared environment, then project `.venv`, with a legacy Conda fallback; check the environment before launch and repair it when checks fail. Added `--check-only`, which exits without launching or repairing. (#577, #599)
- Added pre-flight diagnostics and startup logs, then integrated environment health checks into the current launcher. Fixed interpreter/PATH selection, replaced the unavailable-on-some-Windows-systems `wmic` timestamp command with PowerShell `Get-Date`, and enabled UTF-8 Python console output. (#532, #577, #599)
- Added Linux Noto CJK font detection and installation attempts for supported package managers, with warnings when automatic setup is unavailable. (#577)
- Unified launcher logs as UTF-8 without BOM from the initial line through incremental output, including Windows PowerShell 5.1, so console and file output use the same encoding. Existing log files are not rewritten. (#602)

### Interface, model selection and task control

- Added searchable model selection with an explicit fetch from the configured provider's OpenAI-compatible model-list API. Custom model IDs remain supported; the API check no longer sends the same test twice. (#537, #576)
- Added background subtitle/dubbing tasks with progress updates and pause, resume and stop controls. Added cooperative cancellation checkpoints in long-running ASR, translation and dubbing loops and cancellation of pending parallel work. Stopping is cooperative, not a guarantee that an in-flight operation immediately ends. (#537, #576)
- Added explicit completion markers and checks for required final outputs to reduce false completion after partial failures. Dubbing is shown after subtitle completion for video inputs. (#576)
- Exposed subtitle-length controls for the initial split and final subtitle line, including suggested ranges and a restore-defaults action. (#576)
- Added browser-language detection, normalized language-code handling, a top-right language selector, and language selection through session/query state with configuration fallback. Expanded interface translations for English, Simplified/Traditional Chinese, Spanish, French, Japanese and Russian, including upload controls and ASR/TTS labels. (#576)
- Hid the Streamlit developer toolbar and disabled automatic file-watcher prompts. Fixed the localized GitHub button template, clarified media-selection errors and prevented repeated uploads from causing rerun loops. (#576)

### Media input, recognition and subtitles

- Added audio-only uploads for subtitle generation, with an audio preview and direct preparation of recognition audio. Audio inputs no longer require a placeholder video; burn-in is disabled in the UI without overwriting the saved video preference. The normal web UI does not expose dubbing for audio-only input. (#576)
- Added an input manifest so generated files are not mistaken for the original input. Improved missing/multiple-media detection, reselection, and history archiving for both audio and video. (#576)
- Request MP4 when yt-dlp merges downloaded video/audio, avoiding an unexpected MKV output that the input workflow cannot handle. (#578)
- Added optional `youtube.proxy`: missing/`null` keeps yt-dlp's system/environment discovery, `''` forces direct connections, and a proxy URL explicitly overrides discovery. No proxy software or port is forced. This option applies to yt-dlp, not other API requests or the existing package updater. (#602)
- Fixed Windows Unicode console output in the app and added traceback reporting for background-task failures; the launcher log-file encoding is separately corrected by #602. (#579, #602)
- Corrected ElevenLabs word-level output to use the fields expected by downstream processing and added fallback handling for segments lacking word entries. (#576, #599)
- Unified cloud ASR interval decoding around FFmpeg mono PCM WAV slices, replacing whole-file librosa decoding and inconsistent audio-file encoding in the 302.ai and ElevenLabs paths. (#599)
- Added project-to-global HuggingFace cache fallback, then made Whisper model resolution offline-first: check complete local directories and project/global cached snapshots before fetching missing files. Removed per-segment mirror pings and misleading cache/obsolete Torch messages. Models are still released between stages to manage GPU memory; other components such as alignment models may need their own downloads. (#577, #602)
- Fixed cumulative subtitle drift on media whose audio presentation timestamps contain overlaps or gaps. Audio extraction now reconciles decoded samples with the source clock for video/audio-only inputs and MP3/PCM output paths. Continuous-clock media is covered by regression tests as well. (#601)

### Dependencies and dubbing

- Refreshed application dependency ranges with compatibility bounds. The GPU/ASR stack uses PyTorch/torchaudio 2.8.0, torchvision 0.23.0, WhisperX 3.8.6-compatible releases and TorchCodec 0.7; Transformers stays below 5 and HuggingFace Hub below 1 to respect upstream constraints. (#599)
- Select compatible CUDA 12.8 wheels when the NVIDIA driver supports them, otherwise CUDA 12.6, with CPU/platform fallback where applicable. This supersedes the earlier installer selection described in v3.0.1; users should not mix incompatible Torch-family wheels or infer a required CUDA toolkit version from the driver's capability label. (#599)
- Use maintained PyPI Demucs 4.1-compatible releases with normal dependency resolution instead of the older Git-source/`--no-deps` workaround. Load Demucs only when vocal separation is requested. Removed unused direct dependencies such as MoviePy and Replicate and redundant direct Lightning/resampy requirements. (#599)
- Fixed fractional TTS duration assignment with pandas 3 and serialized new subtitle timestamps as plain floats for NumPy 2 compatibility. Added safe reading of legacy `np.float32(...)`/`np.float64(...)` numeric literals in dubbing task tables, rejecting arbitrary calls instead of evaluating them. Existing task files are read compatibly, not rewritten. (#599, #602)
- Invoke Edge TTS through the active Python interpreter, avoiding an unrelated executable on PATH. (#599)
- GPT-SoVITS readiness now checks its read-only API schema rather than the absent `/ping` endpoint or an arbitrary HTTP response. Added bounded probes, child-exit detection, loopback proxy bypass and child-specific working directories. Custom builds with OpenAPI disabled are not automatically accepted; schema validation does not prove synthesis succeeds. (#602)
- Added focused dependency/audio-timeline/runtime-compatibility regression coverage and an explicitly opt-in media integration suite. The merged documentation records Windows validation and offline compatibility tests; it does not establish that every platform, live download site, provider or TTS backend was retested. (#599, #601, #602)

### Defaults and documentation

- Replaced the obsolete default LLM endpoint/model with **DeepSeek V4 Flash via OpenRouter** (`deepseek/deepseek-v4-flash`). Users still need their own provider credentials; the default does not imply free or included API access. (`814f84e`)
- Vocal separation is now disabled by default in the shipped configuration; subtitle burn-in remains enabled for video inputs. Existing user configuration should be reviewed rather than replaced blindly. (#576, final configuration)
- Updated multilingual READMEs and installation pages for uv, model selection, task controls and provider defaults. Added detailed runtime-dependency and audio-timeline notes. Internal version metadata progressed through 3.0.2 and 3.0.3 during this interval; these commits are consolidated here rather than presented as separately published releases. (#537, #576, #577, #599, #601)

### Upgrade notes

1. Use the environment's Python to run `python installer.py --check` before deciding whether repair or upgrade is needed. `python installer.py --upgrade` refreshes dependencies within the supported ranges. `python setup_env.py --shared` creates/reuses the shared environment; it may offer to recreate an environment using a different Python version. Do not use `--yes` unless that replacement is intended.
2. The installer accepts Python **3.10–3.13**; fresh setup defaults to **3.13**. Python 3.14 is outside the supported range. Keep FFmpeg available on PATH; TorchCodec requires a compatible shared-library FFmpeg build. See [runtime dependency notes](https://github.com/Huanshere/VideoLingo/blob/c28fe34a5a8da008939add4174700ae31fc6be81/docs/runtime-dependencies.md).
3. Check your API endpoint, model and credentials when updating an existing configuration. The new provider default is not a migration of your account or a change to its billing arrangements. Legacy Conda startup remains available, while the documentation recommends uv.
4. Restart the application after a source update because file watching is disabled. Existing recognition audio/subtitles are retained by resume behavior: the timing fix applies to newly extracted audio and does not automatically repair older results. See [audio timeline notes](https://github.com/Huanshere/VideoLingo/blob/c28fe34a5a8da008939add4174700ae31fc6be81/docs/audio-timeline.md).
5. If using explicit download proxies or GPT-SoVITS, review [download networking](https://github.com/Huanshere/VideoLingo/blob/dcf55ff078d3d3fdadcdfdbd2f790539cfbaaab9/docs/download-network.md) and [runtime compatibility](https://github.com/Huanshere/VideoLingo/blob/dcf55ff078d3d3fdadcdfdbd2f790539cfbaaab9/docs/runtime-compatibility.md). Do not publish credentials embedded in proxy URLs. An incomplete explicitly selected local Whisper model directory produces an error instead of silently switching models.

Thanks to **@doomsday616, @phucsd1 and @Huanshere** for the contributions and maintenance in this interval.

[Full changelog: v3.0.1 to the reviewed commit](https://github.com/Huanshere/VideoLingo/compare/v3.0.1...dcf55ff078d3d3fdadcdfdbd2f790539cfbaaab9)

---

## 中文更新说明

本次汇总 v3.0.1 之后已合并的更新：支持本地及共享环境的安装方式、可搜索的模型选择、后台任务控制、纯音频生成字幕、多语言界面完善，以及下载、字幕时间轴和配音兼容性修复。

### 安装与启动

- 新增不依赖 Anaconda 的 uv 安装方式，支持项目内 `.venv`、共享 `~/.venvs/videolingo` 以及自定义环境目录。新建环境当前默认使用 **Python 3.13**。Windows 批处理启动脚本支持项目内的 uv 环境。（#537、#577、#599）
- 新增分阶段的 `installer.py`，支持安装状态记录、依赖版本检查、安装重试、显式强制安装及升级选项，以及可选的 Demucs 安装。`install.py` 继续作为兼容入口。（#577、#599）
- Windows 启动入口统一为 `OneKeyStart.bat`：优先共享环境，其次项目 `.venv`，最后回退到旧 Conda 环境；启动前检查环境，检查失败时执行修复。`--check-only` 只检查，不启动应用，也不自动修复。（#577、#599）
- 新增启动前诊断和日志，后续将环境健康检查整合进当前启动器。修复解释器和 PATH 选择，使用 PowerShell `Get-Date` 替代部分 Windows 已不再提供的 `wmic` 时间戳命令，并启用 Python 控制台 UTF-8 输出。（#532、#577、#599）
- 新增 Linux Noto CJK 字体检测及支持的软件包管理器安装尝试，无法自动安装时给出提示。（#577）
- 启动器日志从首行到持续输出统一使用无 BOM 的 UTF-8，包括 Windows PowerShell 5.1，避免屏幕输出和日志使用不同编码。已有日志文件不会被重写。（#602）

### 界面、模型选择与任务控制

- 新增模型搜索框，可主动从所配置服务的 OpenAI 兼容模型列表接口获取模型，也支持手动填写模型 ID。检查 API 时不再重复发送相同的测试请求。（#537、#576）
- 字幕和配音处理改为后台任务，提供进度、暂停、继续和停止操作。在语音识别、翻译和配音长循环中增加协作式停止检查，并取消尚未执行的并行工作。停止需要处理流程配合，不代表已经发出的请求会立即结束。（#537、#576）
- 增加明确的完成标记和最终输出检查，减少处理只完成一部分却被误判为成功的情况。视频输入在字幕完成后显示配音步骤。（#576）
- 将初次断句和最终字幕行长度设置放到界面，提供建议范围及恢复默认操作。（#576）
- 新增浏览器语言识别、语言代码归一化和右上角语言选择器；语言优先从会话及 URL 参数读取，配置文件作为回退。完善英语、简体中文、繁体中文、西班牙语、法语、日语和俄语界面，包括上传控件及识别、配音选项。（#576）
- 隐藏 Streamlit 开发工具栏并关闭自动文件监听提示。修复 GitHub 按钮的本地化模板，改进媒体选择错误提示，避免重复上传触发循环刷新。（#576）

### 媒体输入、识别与字幕

- 支持上传纯音频生成字幕，可预览音频并直接准备识别音轨，不再需要生成占位视频。音频输入时只在界面禁用字幕压制，不覆盖用户保存的视频压制偏好。当前正常网页流程不向纯音频输入显示配音步骤。（#576）
- 新增输入清单，区分原始媒体与生成文件，避免把配音产物误认为输入。完善媒体缺失、多文件冲突、重新选择及音视频历史归档处理。（#576）
- yt-dlp 合并下载的音视频时指定 MP4，避免输出输入流程无法处理的意外 MKV 文件。（#578）
- 新增可选的 `youtube.proxy`：不填写或 `null` 沿用 yt-dlp 的系统及环境代理发现，`''` 强制直连，代理 URL 则显式覆盖。不强制代理软件或端口，仅影响 yt-dlp，不影响其他 API 请求或现有的软件包更新步骤。（#602）
- 修复 Windows 下应用控制台的 Unicode 输出，并在后台任务失败时打印错误堆栈；启动器日志文件编码另由 #602 修复。（#579、#602）
- 修正 ElevenLabs 的逐词结果字段，使其符合下游处理要求；对缺少逐词条目的片段增加回退处理。（#576、#599）
- 302.ai 和 ElevenLabs 云端识别统一通过 FFmpeg 提取指定区间的单声道 PCM WAV，替代整段音频的 librosa 解码和不一致的音频编码方式。（#599）
- 在项目 HuggingFace 缓存回退到全局缓存的基础上，Whisper 改为优先离线解析：先检查完整的本地目录、项目和全局缓存，再下载缺失文件。移除每段的镜像探测、误导缓存警告及过时 Torch 提示。为控制显存占用仍会在阶段间释放模型；对齐模型等其他组件可能需要独立下载。（#577、#602）
- 修复音轨播放时间标记存在重叠或间隙时，字幕越到后面越偏移的问题。视频和纯音频提取均按原始时间轴校正，覆盖 MP3 及 PCM 输出；连续时间轴也有回归测试。（#601）

### 依赖与配音兼容性

- 更新依赖版本范围并增加兼容性上限。识别及 GPU 组件采用 PyTorch/torchaudio 2.8.0、torchvision 0.23.0、兼容 WhisperX 3.8.6 的版本和 TorchCodec 0.7；为满足上游约束，Transformers 保持低于 5，HuggingFace Hub 保持低于 1。（#599）
- 根据 NVIDIA 驱动能力选择 CUDA 12.8 或 CUDA 12.6 安装包，并为适用的平台提供 CPU 等回退。这替代了 v3.0.1 发布说明中的旧选择逻辑；不要混装不兼容的 Torch 系列组件，也不要把驱动显示的 CUDA 能力误当成必须安装的工具包版本。（#599）
- Demucs 改用 PyPI 上维护的 4.1 兼容版本并正常解析依赖，替代旧的 Git 源码加 `--no-deps` 安装方式；只有请求人声分离时才加载。移除 MoviePy、Replicate 等未使用的直接依赖，以及重复的 Lightning、resampy 直接约束。（#599）
- 修复 pandas 3 下向整数字段写入小数配音时长的错误；新生成的字幕时间改用普通浮点数保存，兼容 NumPy 2。配音任务表新增对旧 `np.float32(...)`、`np.float64(...)` 数字格式的受限解析，拒绝执行任意函数调用。旧任务文件可兼容读取，不会被重写。（#599、#602）
- Edge TTS 使用当前 Python 解释器执行，避免误用 PATH 上其他环境的程序。（#599）
- GPT-SoVITS 改为检查只读 API 结构，不再依赖不存在的 `/ping` 或任意 HTTP 响应。增加有超时限制的探测、子进程退出检测、本地探测绕过外部代理及仅对子进程设置工作目录。关闭 OpenAPI 的自定义版本不会被自动接受，接口结构检查也不等于已成功合成语音。（#602）
- 新增依赖、音频时间轴和运行兼容性的针对性回归测试，以及需主动启用的媒体集成测试。已合并文档记录了 Windows 验证和离线兼容测试，但不代表所有平台、真实下载站点、服务商及配音后端都已重新实测。（#599、#601、#602）

### 默认配置与文档

- 默认大模型服务改为 **通过 OpenRouter 使用 DeepSeek V4 Flash**（`deepseek/deepseek-v4-flash`），替代失效的旧默认配置。用户仍需提供自己的 API 凭据，不代表包含免费调用额度。（`814f84e`）
- 随仓库提供的配置默认关闭人声分离，视频输入的字幕压制仍默认开启。升级时应检查自己的配置，不应直接覆盖。（#576、最终配置）
- 更新多语言 README 和安装文档，介绍 uv、模型搜索、任务控制及新的服务默认值；新增依赖兼容和音频时间轴说明。期间代码中的版本元数据曾更新至 3.0.2、3.0.3，本文统一汇总，不将其写成已经独立发布的 Release。（#537、#576、#577、#599、#601）

### 升级注意事项

1. 先使用环境里的 Python 执行 `python installer.py --check`，再决定是否修复或升级。`python installer.py --upgrade` 在兼容范围内升级依赖。`python setup_env.py --shared` 创建或复用共享环境；遇到不同 Python 版本时可能要求重建，不打算替换环境时不要使用 `--yes`。
2. 安装器支持 **Python 3.10–3.13**，新环境默认 **3.13**，不支持 Python 3.14。FFmpeg 需要在 PATH 中可用；TorchCodec 需要兼容的共享库版 FFmpeg。详见[运行依赖说明](https://github.com/Huanshere/VideoLingo/blob/c28fe34a5a8da008939add4174700ae31fc6be81/docs/runtime-dependencies.md)。
3. 升级现有配置时检查 API 地址、模型及凭据。默认服务变更不会迁移你的账号或改变其计费关系。旧 Conda 启动方式仍有兼容入口，文档推荐使用 uv。
4. 代码更新后需重启应用，因为文件监听已关闭。断点续跑会保留已有识别音频和字幕：时间轴修复针对新提取音频，不会自动修复旧结果。详见[音频时间轴说明](https://github.com/Huanshere/VideoLingo/blob/c28fe34a5a8da008939add4174700ae31fc6be81/docs/audio-timeline.md)。
5. 使用显式下载代理或 GPT-SoVITS 时，请查阅[下载网络配置](https://github.com/Huanshere/VideoLingo/blob/dcf55ff078d3d3fdadcdfdbd2f790539cfbaaab9/docs/download-network.md)和[运行兼容性说明](https://github.com/Huanshere/VideoLingo/blob/dcf55ff078d3d3fdadcdfdbd2f790539cfbaaab9/docs/runtime-compatibility.md)。代理 URL 中的凭据不可公开。显式选择的本地 Whisper 模型目录不完整时会报错，不会悄悄切换模型。

感谢 **@doomsday616、@phucsd1 和 @Huanshere** 在此期间的贡献与维护。

[完整变更：v3.0.1 至本次核对提交](https://github.com/Huanshere/VideoLingo/compare/v3.0.1...dcf55ff078d3d3fdadcdfdbd2f790539cfbaaab9)

---

## Commit coverage / 提交覆盖核对

All commits in the reviewed range are listed below. Merge commits are included
for traceability, not counted as separate user-facing features. PR descriptions
were cross-checked against final source because some intermediate behavior was
superseded later in the range.

以下列出核对范围内的全部提交。合并提交仅用于追溯，不重复计算功能；PR 描述已对照最终代码，避免将被后续替代的中间行为写成当前功能。

| Commit | PR | Coverage / 对应内容 |
| --- | --- | --- |
| `b256ca1` | [#532](https://github.com/Huanshere/VideoLingo/pull/532) | Pre-flight launcher diagnostics and logging / 启动诊断与日志 |
| `29e240d` | #532 merge | Merge of the preceding change / 合并上述改动 |
| `5f0ba8c` | [#537](https://github.com/Huanshere/VideoLingo/pull/537) | uv setup, model search, background task controls, batch launcher, documentation / uv 安装、模型搜索、后台控制、批处理入口与文档 |
| `dfbdc00` | #537 merge | Merge of the preceding change / 合并上述改动 |
| `c93c578` | [#578](https://github.com/Huanshere/VideoLingo/pull/578) | MP4 download merge format / 下载合并输出 MP4 |
| `ee38e19` | [#579](https://github.com/Huanshere/VideoLingo/pull/579) | Unicode console and task tracebacks / Unicode 控制台与任务错误堆栈 |
| `9f9e813` | #578 merge | Merge of the download-format fix / 合并下载格式修复 |
| `8cc6be9` | #579 merge | Merge of the console fix / 合并控制台修复 |
| `3b0fbab` | [#576](https://github.com/Huanshere/VideoLingo/pull/576), squash | Localization, audio-only subtitles, input/completion handling, cancellation, UX and metadata / 多语言、纯音频字幕、输入与完成状态、停止检查、界面与版本元数据 |
| `968268b` | [#577](https://github.com/Huanshere/VideoLingo/pull/577), squash | Stage-based installer, shared environments, launcher, cache fallback, fonts and metadata / 分阶段安装、共享环境、启动器、缓存回退、字体与版本元数据 |
| `814f84e` | Direct commit / 直接提交 | Default provider/model and related documentation / 默认服务、模型及文档 |
| `71dd88d` | [#599](https://github.com/Huanshere/VideoLingo/pull/599) | Dependency compatibility, Python/CUDA selection, cloud audio, dubbing and startup fixes, tests / 依赖兼容、Python/CUDA 选择、云端音频、配音与启动修复及测试 |
| `3ab60de` | [#601](https://github.com/Huanshere/VideoLingo/pull/601) | Presentation-clock extraction and synthetic regressions / 按播放时间轴提取音频与合成回归测试 |
| `6032ae6` | #601 merge | Merge of the timeline fix / 合并时间轴修复 |
| `c28fe34` | #599 merge | Merge of dependency/runtime fixes / 合并依赖及运行修复 |
| `a06de02` | [#602](https://github.com/Huanshere/VideoLingo/pull/602) | Offline-first cache, optional proxy, UTF-8 logs, SoVITS readiness, safe legacy literals / 缓存优先、可选代理、UTF-8 日志、SoVITS 检测、旧数据安全解析 |
| `dcf55ff` | #602 merge | Merge of runtime compatibility fixes; reviewed cutoff / 合并运行兼容修复，本次核对终点 |

Reproduce the scope with `git log --reverse --oneline v3.0.1..dcf55ff` and
`git diff --stat v3.0.1..dcf55ff`. No application tests, package installation or
paid API calls are needed to review this documentation-only proposal.
