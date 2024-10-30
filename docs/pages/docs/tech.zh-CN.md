**Videolingo 视频翻译系统技术文档**

Videolingo 是一个高度集成的视频翻译系统，能够自动化执行视频下载、音频提取、语音识别、字幕生成、文本翻译，以及音视频合成等一系列复杂操作。该系统还提供了一个 Web 界面，用于任务管理和系统配置。

对于开发人员，可以单步执行 `core` 下的每一个 `step__.py` 文件并在 `output` 下检查每一步的输出。

以下是系统的核心技术模块和工作流程：

1. **视频获取模块**:
   - `core/step1_ytdlp.py`: 集成`yt-dlp`库，实现从指定 URL 高效下载视频的功能，并清理文件名。

2. **音频处理与语音识别模块**:
   - `core/all_whisper_methods/whisperX.py`: 使用本地 WhisperX 模型进行转录。
   - `core/all_whisper_methods/whisperXapi.py`: 使用 replicate 的 whisperX 模型进行转录。
   - `core/step2_whisper.py`: 利用 Whisper 模型进行高精度的语音识别，生成带时间戳的文本转录结果。

3. **文本处理与翻译模块**:
   - `core/step3_1_spacy_split.py`: 应用 SpaCy 自然语言处理工具进行初步的文本分割。
   - `core/step3_2_splitbymeaning.py`: 结合 GPT 模型的语义理解能力，对长句进行更精确的分割。
   - `core/step4_1_summarize.py`: 利用 GPT 模型对视频内容进行智能摘要，提取关键术语。
   - `core/step4_2_translate_all.py`: 实现批量化的字幕文本翻译处理。
   - `core/translate_once.py`: 采用三步翻译法（直译、意译和润色）实现高质量的英文到中文的逐句翻译。

4. **字幕处理与合成模块**:
   - `core/step5_splitforsub.py`: 根据字幕格式规范，对翻译后的文本进行精确分割和时间对齐。
   - `core/step6_generate_final_timeline.py`: 生成标准 SRT 格式的字幕文件，包含精确的时间轴信息。
   - `core/step7_merge_sub_to_vid.py`: 实现字幕与视频的无缝集成，使用 ffmpeg 进行处理。

5. **音频处理与配音模块**:
   - `core/step8_gen_audio_task.py`: 生成音频任务，处理字幕以确保与时间相符。
   - `core/step10_gen_audio.py`: 从文本生成音频文件，并根据时间调整语速。
   - `core/step11_merge_audio_to_vid.py`: 将生成的配音音频与视频进行专业级别的合成。
   - `core/delete_retry_dubbing.py`: 删除不必要的音频文件以清理生成过程中的多余文件。

6. **自然语言处理工具集**:
   - `core/ask_gpt.py`: 封装与 GPT 模型交互的标准化接口，用于各类文本生成和分析任务。
   - `core/prompts_storage.py`: 集中管理针对不同任务优化的提示模板。
   - `core/spacy_utils/`: 封装基于 SpaCy 的句子分割等高级文本处理功能。
     - `split_by_connector.py`: 根据连接词拆分文本句子，提高可读性。
     - `split_by_comma.py`: 根据逗号和冒号拆分文本处理。
     - `split_long_by_root.py`: 按句子根节点拆分长句子，增强文本的可读性。
     - `split_by_mark.py`: 用标点符号对文本进行句子拆分。
     - `load_nlp_model.py`: 加载和初始化所需的 NLP 模型，支持多种语言。

7. **文本转语音（TTS）模块**:
   - `core/all_tts_functions/fish_tts.py`: 使用外部 API 实现文本转语音功能，生成音频文件。
   - `core/all_tts_functions/openai_tts.py`: 使用 OpenAI 的 TTS 服务将文本转换为音频并保存。
   - `core/all_tts_functions/gpt_sovits_tts.py`: 使用 GPT-SoVITS 进行文本到语音转换，支持多语言。
   - `core/all_tts_functions/azure_tts.py`: 利用 Azure 语音服务将文本转换为音频，保存为 WAV 格式。

8. **系统配置与工具模块**:
   - `config.yaml`: 集中存储和管理系统的全局参数配置。
   - `install.py`: 自动化系统依赖包和模型的安装与配置过程。
   - `onekeycleanup.py`: 提供一键式中间文件清理功能，优化系统存储空间。
   - `core/config_utils.py`: 读取和更新 YAML 配置文件，确保多线程安全的读写操作。

9. **批量处理模块**:
   - `batch/utils/batch_processor.py`: 批量处理视频任务，通过 Excel 配置管理视频处理流程。
   - `batch/utils/video_processor.py`: 实现视频的下载、转录、分句、翻译和合成带字幕的视频。
   - `batch/utils/settings_check.py`: 检查输入文件与配置的一致性，确保视频处理设置的正确性。

10. **Streamlit 界面模块**:
    - `st.py`: 基于 Streamlit 框架构建的交互式 Web 应用，实现各处理模块的无缝集成。
    - `st_components/download_video_section.py`: 提供 YouTube 链接下载和本地文件上传两种视频获取方式。
    - `st_components/imports_and_utils.py`: 封装界面组件通用的工具函数库。
    - `st_components/sidebar_setting.py`: 实现基于侧边栏的系统设置界面，提供直观的配置管理。

Videolingo 系统通过这些模块的协同工作，实现了从视频下载到最终生成带有翻译字幕和配音的视频的全流程自动化。系统的模块化设计使得每个步骤都可以独立运行和调试，同时也为未来的功能扩展提供了便利。
