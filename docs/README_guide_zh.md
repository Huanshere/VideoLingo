**Videolingo视频翻译系统技术文档**、

Videolingo是一个高度集成的视频翻译系统,能够自动化执行视频下载、音频提取、语音识别、字幕生成、文本翻译,以及音视频合成等一系列复杂操作。该系统还提供了一个Web界面,用于任务管理和系统配置。

对于开发人员，可以单步执行 `core` 下的每一个 `step__.py` 文件并在 `output` 下检查每一步的输出。

以下是系统的核心技术模块和工作流程:

1. **视频获取模块**: 
   - `st_components/download_video_section.py`: 基于Streamlit框架构建的Web应用程序组件,提供YouTube链接下载和本地文件上传两种视频获取方式。
   - `core/step1_ytdlp.py`: 集成`yt_dlp`库,实现从指定URL高效下载视频的功能。

2. **音频处理与语音识别模块**: 
   - `core/all_whisper_methods
   - `core/step2_whisper.py`: 利用OpenAI的Whisper模型进行高精度的语音识别,生成带时间戳的文本转录结果。

3. **文本处理与翻译模块**: 
   - `core/step3_1_spacy_split.py`: 应用SpaCy自然语言处理工具进行初步的文本分割。
   - `core/step3_2_splitbymeaning.py`: 结合GPT模型的语义理解能力,对长句进行更精确的分割。 
   - `core/step4_1_summarize.py`: 利用GPT模型对视频内容进行智能摘要,提取关键术语。
   - `core/step4_2_translate_all.py`: 实现批量化的字幕文本翻译处理。
   - `core/step4_2_translate_once.py`: 采用三步翻译法(直译、意译和润色)实现高质量的英文到中文的逐句翻译。

4. **字幕处理与合成模块**:
   - `core/step5_splitforsub.py`: 根据字幕格式规范,对翻译后的文本进行精确分割和时间对齐。 
   - `core/step6_generate_final_timeline.py`: 生成标准SRT格式的字幕文件,包含精确的时间轴信息。
   - `core/step7_merge_sub_to_vid.py`: 实现字幕与视频的无缝集成。

5. **音频处理与配音模块**（⚠️暂时停用）:
   - `core/step8_extract_refer_audio.py`: 从源视频中提取关键音频片段作为参考。
   - `core/step9_generate_audio_task.py`: 基于翻译后的字幕内容,生成结构化的音频合成任务。
   - `core/step10_generate_audio.py`: 利用先进的SoVITS模型生成高质量的配音音频。
   - `core/step11_merge_audio_to_vid.py`: 将生成的配音音频与视频进行专业级别的合成。

6. **自然语言处理工具集**:
   - `core/ask_gpt.py`: 封装与GPT模型交互的标准化接口,用于各类文本生成和分析任务。
   - `core/prompts_storage.py`: 集中管理针对不同任务优化的提示模板。
   - `core/spacy_utils/`: 封装基于SpaCy的句子分割等高级文本处理功能。

7. **系统配置与工具模块**:
   - `config.py`: 集中存储和管理系统的全局参数配置。
   - `st.py`: 基于Streamlit框架构建的交互式Web应用,实现各处理模块的无缝集成。
   - `install.py`: 自动化系统依赖包和模型的安装与配置过程。
   - `onekeycleanup.py`: 提供一键式中间文件清理功能,优化系统存储空间。
   - `st_components/imports_and_utils.py`: 封装界面组件通用的工具函数库。 
   - `st_components/sidebar_setting.py`: 实现基于侧边栏的系统设置界面,提供直观的配置管理。