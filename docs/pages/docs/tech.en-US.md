**Videolingo Video Translation System Technical Documentation**

Videolingo is a highly integrated video translation system capable of automatically executing a series of complex operations including video downloading, audio extraction, speech recognition, subtitle generation, text translation, and audio-video synthesis. The system also provides a web interface for task management and system configuration.

For developers, each `step__.py` file under the `core` directory can be executed step by step, and the output of each step can be checked under the `output` directory.

The following are the core technical modules and workflow of the system:

1. **Video Acquisition Module**: 
   - `st_components/download_video_section.py`: A web application component built on the Streamlit framework, providing two methods of video acquisition: YouTube link download and local file upload.
   - `core/step1_ytdlp.py`: Integrates the `yt_dlp` library to efficiently download videos from specified URLs.

2. **Audio Processing and Speech Recognition Module**: 
   - `core/all_whisper_methods`: Different Whisper method options.
   - `core/step2_whisper.py`: Utilizes the Whisper model for high-precision speech recognition, generating text transcription results with timestamps.

3. **Text Processing and Translation Module**: 
   - `core/step3_1_spacy_split.py`: Applies SpaCy natural language processing tools for preliminary text segmentation.
   - `core/step3_2_splitbymeaning.py`: Combines GPT model's semantic understanding capability for more precise segmentation of long sentences. 
   - `core/step4_1_summarize.py`: Uses GPT model for intelligent summarization of video content and extraction of key terms.
   - `core/step4_2_translate_all.py`: Implements batch processing of subtitle text translation.
   - `core/translate_once.py`: Employs a three-step translation method (literal translation, free translation, and polishing) to achieve high-quality sentence-by-sentence translation from English to Chinese.

4. **Subtitle Processing and Synthesis Module**:
   - `core/step5_splitforsub.py`: Precisely segments and time-aligns translated text according to subtitle format specifications. 
   - `core/step6_generate_final_timeline.py`: Generates standard SRT format subtitle files with precise timeline information.
   - `core/step7_merge_sub_to_vid.py`: Achieves seamless integration of subtitles with video.

5. **Audio Processing and Dubbing Module** (⚠️ Temporarily disabled):
   - `core/step8_extract_refer_audio.py`: Extracts key audio segments from the source video as references.
   - `core/step9_generate_audio_task.py`: Generates structured audio synthesis tasks based on translated subtitle content.
   - `core/step10_generate_audio.py`: Utilizes the advanced SoVITS model to generate high-quality dubbing audio.
   - `core/step11_merge_audio_to_vid.py`: Performs professional-level synthesis of generated dubbing audio with video.

6. **Natural Language Processing Toolkit**:
   - `core/ask_gpt.py`: Encapsulates a standardized interface for interacting with GPT models, used for various text generation and analysis tasks.
   - `core/prompts_storage.py`: Centrally manages optimized prompt templates for different tasks.
   - `core/spacy_utils/`: Encapsulates advanced text processing functions based on SpaCy, such as sentence segmentation.

7. **System Configuration and Utility Module**:
   - `config.py`: Centrally stores and manages global parameter configurations for the system.
   - `st.py`: An interactive web application built on the Streamlit framework, achieving seamless integration of various processing modules.
   - `install.py`: Automates the installation and configuration process of system dependencies and models.
   - `onekeycleanup.py`: Provides one-click intermediate file cleanup functionality to optimize system storage space.
   - `st_components/imports_and_utils.py`: Encapsulates a library of common utility functions for interface components. 
   - `st_components/sidebar_setting.py`: Implements a sidebar-based system settings interface, providing intuitive configuration management.