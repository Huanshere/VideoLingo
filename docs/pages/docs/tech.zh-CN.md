## Videolingo 视频翻译系统技术文档

Videolingo 是一个高度集成的视频翻译系统，能够自动执行一系列复杂的操作，包括视频下载、音频提取、语音识别、文本处理、翻译、字幕生成、文本到语音合成以及音视频合成。该系统利用 AI 技术（ASR、NLP、LLMs、TTS），并提供用于批量处理的命令行界面和使用 Streamlit 的交互式 Web 界面，用于任务管理和系统配置。

该项目已经过重大重构，形成了一个更加模块化和健壮的结构。核心功能现在组织成不同的包和模块，主要位于 `core` 目录及其子目录（`asr_backend`、`spacy_utils`、`st_utils`、`tts_backend`、`utils`）中，以及一个专门的 `batch` 目录用于批量处理实用程序，以及一个 `translations` 目录用于国际化。

对于开发人员来说，`core` 目录中的许多组件（尤其是编号为 `_X_*.py` 的文件）代表处理管道中的不同步骤，并且可以单独执行以进行调试。中间输出和最终输出通常存储在 `output` 目录中，并具有清理和归档到 `history` 目录的机制。

以下概述核心技术模块和工作流程：

**1. 安装和设置：**

*   `install.py`: 主要安装脚本。自动化依赖项安装（包括带有 GPU/CPU 检测的 PyTorch）、环境配置（语言、PyPI 镜像）、FFmpeg 检查、Noto 字体安装 (Linux) 以及启动 Streamlit 应用程序。
*   `setup.py`: 标准 Python 项目设置文件，使用 `setuptools`。定义项目元数据（名称、版本）和依赖项（从 `requirements.txt` 读取），用于通过 pip 进行打包和安装。

**2. 视频获取模块：**

*   `core/_1_ytdlp.py`: 集成 `yt-dlp` 库以从 URL 下载视频。处理 `yt-dlp` 更新、文件名清理、分辨率选择以及用于身份验证下载的 cookie 用法。还包括一个在输出目录中查找单个视频文件的函数。

**3. 音频处理和语音识别 (ASR) 模块 (`core/asr_backend`):**

*   `core/asr_backend/demucs_vl.py`: 使用 Demucs 模型 (`htdemucs`) 将音频分离为人声和背景音轨，从而提高后续 ASR 的质量。
*   `core/asr_backend/audio_preprocess.py`: 包含准备音频的基本功能：音量标准化 (`pydub`)、视频到音频的转换 (`ffmpeg`)、静音检测 (`ffmpeg`)、音频时长计算 (`ffmpeg`)、将长音频文件拆分为可管理的片段、将 ASR 结果处理为 DataFrames、保存结果以及存储检测到的语言。
*   `core/asr_backend/whisperX_local.py`: 使用 WhisperX 库实现本地音频转录。根据可用硬件（GPU/CPU）优化性能，处理模型下载（具有镜像检查），执行转录和对齐，调整时间戳，并管理 GPU 内存。
*   `core/asr_backend/whisperX_302.py`: 使用 302.ai WhisperX API 实现音频转录，包括缓存和时间戳调整。
*   `core/asr_backend/elevenlabs_asr.py`: 使用 ElevenLabs 语音转文本 API 实现音频转录，处理音频切片、API 交互、格式转换（ElevenLabs 到类似 Whisper 的格式）和临时文件管理。
*   `core/_2_asr.py`: 编排 ASR 过程。提取音频，可选择执行 Demucs 人声分离，拆分音频，调用配置的 ASR 后端（本地 WhisperX、302 API 或 Elevenlabs API），合并结果，将转录处理为 DataFrame，并保存输出。

**4. 文本处理和翻译模块 (`core`, `core/spacy_utils`):**

*   **句子拆分 (`core/spacy_utils`):**
    *   `core/spacy_utils/load_nlp_model.py`: 根据检测到的语言加载和初始化适当的 spaCy NLP 模型，如果需要，处理模型下载。
    *   `core/spacy_utils/split_by_mark.py`: 使用 spaCy 基于标点符号执行初始句子拆分，并特殊处理破折号和省略号。
    *   `core/spacy_utils/split_by_comma.py`: 基于逗号进一步细化句子拆分，使用 spaCy 分析语法有效性。
    *   `core/spacy_utils/split_by_connector.py`: 使用 spaCy 基于语言连接词（连词、关系代词）拆分句子，支持多种语言。
    *   `core/spacy_utils/split_long_by_root.py`: 使用 spaCy 的依赖关系解析（识别句子主语）和基于回退长度的拆分来拆分过长的句子。
    *   `core/_3_1_split_nlp.py`: 编排基于 spaCy 的拆分过程，调用各种拆分函数（`split_by_mark`、`split_by_comma_main`、`split_sentences_main`、`split_long_by_root_main`）。
*   **基于含义的拆分和翻译：**
    *   `core/_3_2_split_meaning.py`: 使用 GPT 模型根据语义智能地拆分长句子，确保翻译和字幕的单元更短、更易于管理。利用 `core/prompts.py` 中定义的提示。
    *   `core/_4_1_summarize.py`: 使用 LLM (GPT) 生成视频脚本的摘要并提取相关术语（可以选择使用 `custom_terms.xlsx` 中的自定义术语进行增强）。将结果保存到 JSON 文件。利用 `core/prompts.py` 中定义的提示。
    *   `core/translate_lines.py`: 使用 GPT 模型实现核心的逐行翻译逻辑。采用两步法（忠实性和表达性）进行高质量翻译，结合上下文提示和重试机制。利用 `core/prompts.py` 中定义的提示。
    *   `core/_4_2_translate.py`: 管理整体翻译过程。将文本拆分为块，收集上下文，调用 `core/translate_lines.py` 进行并行块翻译，检查翻译质量（相似性），对齐时间戳，修剪文本以适应音频时长，并将结果保存到 Excel。

**5. 字幕处理和合成模块 (`core`):**

*   `core/_5_split_sub.py`: 将长的翻译字幕拆分为适合显示的较短片段，使用加权长度计算和基于 GPT 的与源字幕的对齐。利用 `core/prompts.py` 中定义的提示。
*   `core/_6_gen_sub.py`: 生成最终的 SRT 字幕文件。将翻译后的文本与源时间戳对齐，清理文本，格式化时间戳，处理小间隙，并为显示和音频配音生成各种 SRT 输出格式（源、翻译、组合）。
*   `core/_7_sub_into_vid.py`: 使用 `ffmpeg` 将生成的 SRT 字幕（源和翻译）直接合并（"烧录"）到视频文件中，具有可自定义的样式和 GPU 加速支持。如果禁用烧录，则创建一个占位符视频。

**6. 音频配音模块 (`core`, `core/tts_backend`):**

*   `core/_8_1_audio_task.py`: 解析 SRT 文件，合并短字幕，清理文本，使用 LLM 根据估计的时长修剪文本，并生成一个 Excel 文件 (`_8_1_AUDIO_TASK.xlsx`)，用于定义 TTS 引擎的任务。利用 `core/prompts.py` 中定义的提示。
*   `core/_8_2_dub_chunks.py`: 分析音频任务文件，计算时间间隙和语速，根据速度和停顿确定配音块的最佳切断点，必要时合并行，匹配字幕，并更新任务文件。
*   `core/_9_refer_audio.py`: 基于音频任务文件中定义的时间戳，从源人声音轨中提取特定的音频片段，创建某些 TTS 引擎（如 GPT-SoVITS、F5-TTS、FishTTS）使用的参考音频文件。
*   **TTS 后端 (`core/tts_backend`):**
    *   `core/tts_backend/azure_tts.py`: Azure 文本转语音 API 的接口。
    *   `core/tts_backend/custom_tts.py`: 用于集成自定义 TTS 引擎的占位符/模板。
    *   `core/tts_backend/edge_tts.py`: 使用 `edge-tts` 命令行工具的 Microsoft Edge TTS 的接口。
    *   `core/tts_backend/fish_tts.py`: 302.ai Fish TTS API 的接口。
    *   `core/tts_backend/gpt_sovits_tts.py`: 本地 GPT-SoVITS 服务器的接口，包括服务器启动逻辑。
    *   `core/tts_backend/openai_tts.py`: OpenAI 文本转语音 API 的接口。
    *   `core/tts_backend/sf_cosyvoice2.py`: SiliconFlow CosyVoice2 TTS API 的接口，支持参考音频。
    *   `core/tts_backend/sf_fishtts.py`: SiliconFlow Fish TTS API 的接口，支持具有参考音频的预设、自定义和动态语音模式。
    *   `core/tts_backend/_302_f5tts.py`: 302.ai F5-TTS API 的接口，使用参考音频进行语音克隆。
    *   `core/tts_backend/estimate_duration.py`: 提供根据特定语言的音节计数和标点符号停顿来估计文本的说话时长的函数。用于音频任务生成和字幕修剪。
    *   `core/tts_backend/tts_main.py`: 中央 TTS 调度器。清理输入文本，根据配置 (`load_key("tts_method")`) 选择适当的 TTS 后端，调用相应的 TTS 函数，使用重试和基于 GPT 的文本纠正来处理错误，验证音频时长，并保存输出 WAV 文件。
*   `core/_10_gen_audio.py`: 使用选定的 TTS 后端通过 `tts_main.py` 生成单独的音频片段。基于计算的因子调整生成的音频速度 (`ffmpeg`) 以适应任务文件中指定的目标时长，并将片段合并为块。使用 `ThreadPoolExecutor` 处理并行处理。
*   `core/_11_merge_audio.py`: 将生成的和速度调整的音频片段（来自 `output/audio_segments/` 的 `.wav` 文件）合并为单个连续的配音音轨 (`output/dub.wav`)，根据字幕时序添加静音。 还生成相应的 SRT 文件 (`output/dub.srt`)。
*   `core/_12_dub_to_vid.py`: 配音的最终合成步骤。使用 `ffmpeg` 合并原始视频、生成的配音音轨 (`output/dub.wav`) 和分离的背景音乐 (`output/background.mp3`，如果使用了 Demucs)。可选择在此过程中烧录字幕。包括音频标准化。

**7. 核心实用程序和配置 (`core/utils`):**

*   `core/prompts.py`: 定义标准化的提示模板，用于指导 LLM（GPT）完成诸如句子拆分、摘要、翻译（忠实性/表达性）、字幕对齐以及文本优化/校正以进行 TTS 等任务。
*   `core/utils/ask_gpt.py`: 提供一个强大的接口（`ask_gpt` 函数）用于与 OpenAI GPT 模型交互。 包括缓存（基于文件）、JSON 响应修复 (`json_repair`)、响应验证、带重试的错误处理 (`@except_handler`) 和日志记录。
*   `core/utils/config_utils.py`: 实用程序函数 (`load_key`, `update_key`)，用于使用 `ruamel.yaml`（保留格式）和 `threading.Lock` 以线程安全的方式从 `config.yaml` 加载和更新配置设置。包括 `get_joiner` 用于特定语言的文本连接。
*   `core/utils/decorator.py`: 定义可重用的装饰器：`except_handler` 用于向函数添加重试逻辑和错误报告，`check_file_exists` 用于如果输出文件已存在则跳过函数执行。 使用 `rich` 进行格式化的输出。
*   `core/utils/delete_retry_dubbing.py`: 提供一个函数 (`delete_dubbing_files`) 来清理与配音过程相关的特定中间文件和目录（例如，`dub.wav`、`output_dub.mp4`、`output/audio/segs`）。
*   `core/utils/onekeycleanup.py`: 实现 `cleanup` 函数，用于将文件从 `output` 目录组织和归档到基于视频名称的结构化的 `history` 目录中。包括文件名清理和强大的文件移动/删除逻辑。
*   `core/utils/pypi_autochoose.py`: 用于自动测试和选择最快的 PyPI 镜像并配置 pip 以使用它的实用程序。 使用 `rich` 进行 UI。
*   `core/utils/models.py`: 定义表示整个管道中使用的各种中间文件和输出文件的文件路径的常量。
*   `core/__init__.py`, `core/asr_backend/__init__.py`, `core/spacy_utils/__init__.py`, `core/st_utils/__init__.py`, `core/tts_backend/__init__.py`: 包初始化文件，定义其各自包/子包的公共接口 (`__all__`)。
*   `core/__init__.py`: 初始化主 `core` 包，从子包导出关键函数和模块，以便更轻松地访问。

**8. 批量处理模块 (`batch`):**

*   `batch/utils/settings_check.py`: 根据 `batch/input` 中的视频文件验证 `batch/tasks_setting.xlsx` 中定义的设置，检查文件是否存在、有效的 URL 和正确的配置值（例如，配音标志）。使用 `rich` 进行输出。
*   `batch/utils/video_processor.py`: 定义 `process_video` 函数，该函数编排批处理作业中*单个*视频的处理管道。 处理输入（URL 或本地文件），调用核心处理步骤（转录、翻译、字幕、可选配音），并进行重试，管理输出文件夹，并调用 `cleanup`。
*   `batch/utils/batch_processor.py`: 批量处理的主协调器。从 `batch/tasks_setting.xlsx` 读取任务（使用 `pandas`），迭代任务，验证设置 (`settings_check.py`)，管理语言配置更改，为每个视频调用 `video_processor.py`，处理错误并重试（包括从 ERROR 文件夹恢复文件），并更新 Excel 文件中的状态。 使用 `rich` 进行控制台输出。

**9. Streamlit 界面模块 (`core/st_utils`, `st.py`):**

*   `core/st_utils/download_video_section.py`: 实现用于选择输入视频的 Streamlit UI 部分，允许用户从 YouTube 下载（使用 `core/_1_ytdlp.py`）或上传本地文件（视频或音频，使用 `ffmpeg` 进行音频到视频的转换）。
*   `core/st_utils/sidebar_setting.py`: 在 Streamlit UI 中创建配置侧边栏。 允许用户设置显示语言、LLM 参数（API 密钥、模型、基本 URL）、字幕设置（识别/目标语言、Demucs 开关、烧录开关）和配音设置（TTS 方法和相关参数，如语音、API 密钥）。使用 `core/utils/config_utils.py` 加载/保存设置，并在更改时触发 `st.rerun()`。包括 API 密钥验证。
*   `core/st_utils/imports_and_utils.py`: 包含 Streamlit 应用程序的通用导入和实用程序函数，例如创建压缩字幕文件的下载按钮的函数以及按钮的 CSS 样式。
*   `st.py`: Streamlit Web 应用程序的主要入口点。设置页面配置，显示徽标，使用 `sidebar_setting.py` 创建侧边栏，管理主 UI 部分（通过 `download_video_section.py` 进行视频下载/上传，文本处理，音频处理），并根据用户交互（按钮点击）触发核心处理函数（`process_text`，`process_audio`）。使用 `st.spinner` 指示长时间操作期间的进度。

**10. 国际化模块 (`translations`):**

*   `translations/translations.py`: 实现 UI 的翻译功能。 定义支持的显示语言，根据选定的语言 (`load_key("display_language")`) 从 JSON 文件加载翻译字符串，并提供 `translate(key)` 函数来检索翻译后的文本，如果缺少翻译，则回退到原始键。

Videolingo实现了从视频获取到最终生成具有翻译字幕和配音的视频的完整流程自动化。 增强的模块化设计使每个步骤都可以更轻松地运行和调试，通过多个后端选项（ASR、TTS）提供更大的灵活性，并为交互式和批量处理工作流程提供改进的配置管理和用户界面。