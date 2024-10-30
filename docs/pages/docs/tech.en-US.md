**Videolingo Video Translation System Technical Documentation**

Videolingo is a highly integrated video translation system capable of automating a series of complex operations including video downloading, audio extraction, speech recognition, subtitle generation, text translation, and audio-video synthesis. The system also provides a web interface for task management and system configuration.

For developers, each `step__.py` file under the `core` directory can be executed individually, and the output of each step can be checked under the `output` directory.

The following are the core technical modules and workflow of the system:

1. **Video Acquisition Module**:
   - `core/step1_ytdlp.py`: Integrates the `yt-dlp` library to efficiently download videos from specified URLs and clean up filenames.

2. **Audio Processing and Speech Recognition Module**:
   - `core/all_whisper_methods/whisperX.py`: Uses local WhisperX model for transcription.
   - `core/all_whisper_methods/whisperXapi.py`: Uses replicate's WhisperX model for transcription.
   - `core/step2_whisper.py`: Utilizes the Whisper model for high-precision speech recognition, generating text transcripts with timestamps.

3. **Text Processing and Translation Module**:
   - `core/step3_1_spacy_split.py`: Applies SpaCy natural language processing tools for initial text segmentation.
   - `core/step3_2_splitbymeaning.py`: Combines GPT model's semantic understanding capability for more precise segmentation of long sentences.
   - `core/step4_1_summarize.py`: Uses GPT model to intelligently summarize video content and extract key terms.
   - `core/step4_2_translate_all.py`: Implements batch processing of subtitle text translation.
   - `core/translate_once.py`: Adopts a three-step translation method (literal translation, free translation, and polishing) to achieve high-quality English to Chinese sentence-by-sentence translation.

4. **Subtitle Processing and Synthesis Module**:
   - `core/step5_splitforsub.py`: Performs precise segmentation and time alignment of translated text according to subtitle format specifications.
   - `core/step6_generate_final_timeline.py`: Generates standard SRT format subtitle files with accurate timeline information.
   - `core/step7_merge_sub_to_vid.py`: Achieves seamless integration of subtitles with video using ffmpeg for processing.

5. **Audio Processing and Dubbing Module**:
   - `core/step8_gen_audio_task.py`: Generates audio tasks, processing subtitles to ensure time consistency.
   - `core/step10_gen_audio.py`: Generates audio files from text and adjusts speech rate according to timing.
   - `core/step11_merge_audio_to_vid.py`: Performs professional-level synthesis of generated dubbing audio with video.
   - `core/delete_retry_dubbing.py`: Deletes unnecessary audio files to clean up excess files generated during the process.

6. **Natural Language Processing Toolkit**:
   - `core/ask_gpt.py`: Encapsulates a standardized interface for interacting with GPT models, used for various text generation and analysis tasks.
   - `core/prompts_storage.py`: Centrally manages optimized prompt templates for different tasks.
   - `core/spacy_utils/`: Encapsulates advanced text processing functions based on SpaCy, such as sentence segmentation.
     - `split_by_connector.py`: Splits text sentences based on connectors to improve readability.
     - `split_by_comma.py`: Splits text processing based on commas and colons.
     - `split_long_by_root.py`: Splits long sentences by sentence root nodes to enhance text readability.
     - `split_by_mark.py`: Uses punctuation marks for sentence splitting in text.
     - `load_nlp_model.py`: Loads and initializes required NLP models, supporting multiple languages.

7. **Text-to-Speech (TTS) Module**:
   - `core/all_tts_functions/fish_tts.py`: Implements text-to-speech functionality using external APIs to generate audio files.
   - `core/all_tts_functions/openai_tts.py`: Uses OpenAI's TTS service to convert text to audio and save it.
   - `core/all_tts_functions/gpt_sovits_tts.py`: Uses GPT-SoVITS for text-to-speech conversion, supporting multiple languages.
   - `core/all_tts_functions/azure_tts.py`: Utilizes Azure Speech Service to convert text to audio, saving in WAV format.

8. **System Configuration and Utility Module**:
   - `config.yaml`: Centrally stores and manages global parameter configurations for the system.
   - `install.py`: Automates the installation and configuration process of system dependencies and models.
   - `onekeycleanup.py`: Provides one-click intermediate file cleanup functionality to optimize system storage space.
   - `core/config_utils.py`: Reads and updates YAML configuration files, ensuring thread-safe read and write operations.

9. **Batch Processing Module**:
   - `batch/utils/batch_processor.py`: Batch processes video tasks, managing video processing workflows through Excel configuration.
   - `batch/utils/video_processor.py`: Implements video downloading, transcription, sentence segmentation, translation, and synthesis of videos with subtitles.
   - `batch/utils/settings_check.py`: Checks the consistency of input files and configurations to ensure the correctness of video processing settings.

10. **Streamlit Interface Module**:
    - `st.py`: An interactive web application built on the Streamlit framework, integrating various processing modules seamlessly.
    - `st_components/download_video_section.py`: Provides two video acquisition methods: YouTube link downloading and local file uploading.
    - `st_components/imports_and_utils.py`: Encapsulates common utility functions for interface components.
    - `st_components/sidebar_setting.py`: Implements a sidebar-based system settings interface, providing intuitive configuration management.

The Videolingo system achieves full-process automation from video downloading to the final generation of videos with translated subtitles and dubbing through the collaborative work of these modules. The modular design of the system allows each step to be run and debugged independently, while also providing convenience for future functional expansions.
