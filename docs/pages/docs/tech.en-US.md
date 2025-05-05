## Videolingo Video Translation System Technical Documentation

Videolingo is a highly integrated video translation system capable of automatically executing a series of complex operations, including video downloading, audio extraction, speech recognition, text processing, translation, subtitle generation, text-to-speech synthesis, and audio-video synthesis. The system leverages AI technologies (ASR, NLP, LLMs, TTS) and provides both a command-line interface for batch processing and an interactive web interface using Streamlit for task management and system configuration.

The project has undergone significant refactoring, resulting in a more modular and robust architecture. Core functionalities are now organized into distinct packages and modules, primarily located within the `core` directory and its subdirectories (`asr_backend`, `spacy_utils`, `st_utils`, `tts_backend`, `utils`), as well as a dedicated `batch` directory for batch processing utilities, and a `translations` directory for internationalization.

For developers, many components within the `core` directory – especially files named with the `_X_*.py` numbering scheme – represent distinct steps in the processing pipeline and can be executed individually for debugging purposes. Intermediate and final outputs are typically stored in the `output` directory, with mechanisms for cleanup and archival to the `history` directory.

The following outlines the core technical modules and workflows:

**1. Installation and Setup:**

*   `install.py`: The primary installation script. Automates dependency installation (including PyTorch with GPU/CPU detection), environment configuration (languages, PyPI mirror), FFmpeg checks, Noto font installation (Linux), and launching the Streamlit application.
*   `setup.py`: A standard Python project setup file, utilizing `setuptools`. Defines project metadata (name, version) and dependencies (read from `requirements.txt`) for packaging and installation via pip.

**2. Video Acquisition Module:**

*   `core/_1_ytdlp.py`: Integrates the `yt-dlp` library to download videos from URLs. Handles `yt-dlp` updates, filename sanitization, resolution selection, and cookie usage for authenticated downloads. Also includes a function to locate a single video file within the output directory.

**3. Audio Processing and Speech Recognition (ASR) Module (`core/asr_backend`):**

*   `core/asr_backend/demucs_vl.py`: Employs the Demucs model (`htdemucs`) to separate audio into vocal and background tracks, improving the quality of subsequent ASR.
*   `core/asr_backend/audio_preprocess.py`: Contains fundamental functions for preparing audio: volume normalization (`pydub`), video-to-audio conversion (`ffmpeg`), silence detection (`ffmpeg`), audio duration calculation (`ffmpeg`), splitting long audio files into manageable segments, processing ASR results into DataFrames, saving results, and storing detected languages.
*   `core/asr_backend/whisperX_local.py`: Implements local audio transcription using the WhisperX library. Optimizes performance based on available hardware (GPU/CPU), handles model downloads (with mirror checking), performs transcription and alignment, adjusts timestamps, and manages GPU memory.
*   `core/asr_backend/whisperX_302.py`: Implements audio transcription using the 302.ai WhisperX API, including caching and timestamp adjustment.
*   `core/asr_backend/elevenlabs_asr.py`: Implements audio transcription using the ElevenLabs Speech to Text API, handling audio slicing, API interaction, format conversion (ElevenLabs to Whisper-like format), and temporary file management.
*   `core/_2_asr.py`: Orchestrates the ASR process. Extracts audio, optionally performs Demucs vocal separation, splits audio, invokes the configured ASR backend (local WhisperX, 302 API, or Elevenlabs API), merges results, processes transcriptions into a DataFrame, and saves the output.

**4. Text Processing and Translation Module (`core`, `core/spacy_utils`):**

*   **Sentence Splitting (`core/spacy_utils`):**
    *   `core/spacy_utils/load_nlp_model.py`: Loads and initializes the appropriate spaCy NLP model based on the detected language, handling model downloads if necessary.
    *   `core/spacy_utils/split_by_mark.py`: Performs initial sentence splitting using spaCy based on punctuation marks, with special handling for dashes and ellipses.
    *   `core/spacy_utils/split_by_comma.py`: Further refines sentence splitting based on commas, utilizing spaCy to analyze grammatical validity.
    *   `core/spacy_utils/split_by_connector.py`: Splits sentences based on linguistic connectors (conjunctions, relative pronouns) using spaCy, supporting multiple languages.
    *   `core/spacy_utils/split_long_by_root.py`: Splits overly long sentences using spaCy's dependency parsing (identifying sentence subjects) and fallback length-based splitting.
    *   `core/_3_1_split_nlp.py`: Orchestrates the spaCy-based splitting process, calling the various splitting functions (`split_by_mark`, `split_by_comma_main`, `split_sentences_main`, `split_long_by_root_main`).
*   **Meaning-Based Splitting and Translation:**
    *   `core/_3_2_split_meaning.py`: Intelligently splits long sentences based on semantics using a GPT model, ensuring shorter and more manageable units for translation and subtitling. Leverages prompts defined in `core/prompts.py`.
    *   `core/_4_1_summarize.py`: Uses an LLM (GPT) to generate summaries of video scripts and extract relevant terms (optionally augmented with custom terms from `custom_terms.xlsx`). Saves results to a JSON file. Leverages prompts defined in `core/prompts.py`.
    *   `core/translate_lines.py`: Implements the core line-by-line translation logic using a GPT model. Employs a two-step approach (fidelity and expressiveness) for high-quality translation, incorporating context prompting and retry mechanisms. Leverages prompts defined in `core/prompts.py`.
    *   `core/_4_2_translate.py`: Manages the overall translation process. Splits text into chunks, gathers context, calls `core/translate_lines.py` for parallel chunk translation, checks translation quality (similarity), aligns timestamps, trims text to fit audio durations, and saves results to Excel.

**5. Subtitle Processing and Synthesis Module (`core`):**

*   `core/_5_split_sub.py`: Splits long translated subtitles into shorter segments suitable for display, using weighted length calculations and GPT-based alignment with source subtitles. Leverages prompts defined in `core/prompts.py`.
*   `core/_6_gen_sub.py`: Generates the final SRT subtitle files. Aligns translated text with source timestamps, cleans text, formats timestamps, handles small gaps, and generates various SRT output formats (source, translated, combined) for display and audio dubbing.
*   `core/_7_sub_into_vid.py`: Merges ("burns") the generated SRT subtitles (source and translated) directly into the video file using `ffmpeg`, with customizable styling and GPU acceleration support. If burning is disabled, creates a placeholder video.

**6. Audio Dubbing Module (`core`, `core/tts_backend`):**

*   `core/_8_1_audio_task.py`: Parses the SRT file, merges short subtitles, cleans the text, trims text based on estimated duration using an LLM, and generates an Excel file (`_8_1_AUDIO_TASK.xlsx`) defining the tasks for the TTS engine. Leverages prompts defined in `core/prompts.py`.
*   `core/_8_2_dub_chunks.py`: Analyzes the audio task file, calculates time gaps and speaking rates, determines optimal cut points for dubbing chunks based on speed and pauses, merges lines where necessary, matches subtitles, and updates the task file.
*   `core/_9_refer_audio.py`: Extracts specific audio segments from the source vocal track based on timestamps defined in the audio task file, creating reference audio files used by certain TTS engines (e.g., GPT-SoVITS, F5-TTS, FishTTS).
*   **TTS Backends (`core/tts_backend`):**
    *   `core/tts_backend/azure_tts.py`: Interface to the Azure Text-to-Speech API.
    *   `core/tts_backend/custom_tts.py`: Placeholder/template for integrating custom TTS engines.
    *   `core/tts_backend/edge_tts.py`: Interface to Microsoft Edge TTS using the `edge-tts` command-line tool.
    *   `core/tts_backend/fish_tts.py`: Interface to the 302.ai Fish TTS API.
    *   `core/tts_backend/gpt_sovits_tts.py`: Interface to a local GPT-SoVITS server, including server startup logic.
    *   `core/tts_backend/openai_tts.py`: Interface to the OpenAI Text-to-Speech API.
    *   `core/tts_backend/sf_cosyvoice2.py`: Interface to the SiliconFlow CosyVoice2 TTS API, supporting reference audio.
    *   `core/tts_backend/sf_fishtts.py`: Interface to the SiliconFlow Fish TTS API, supporting preset, custom, and dynamic voice modes with reference audio.
    *   `core/tts_backend/_302_f5tts.py`: Interface to the 302.ai F5-TTS API, which uses reference audio for voice cloning.
    *   `core/tts_backend/estimate_duration.py`: Provides functions to estimate the speaking duration of text based on syllable counts and punctuation pauses for a given language. Used for audio task generation and subtitle trimming.
    *   `core/tts_backend/tts_main.py`: Central TTS dispatcher. Cleans input text, selects the appropriate TTS backend based on configuration (`load_key("tts_method")`), calls the corresponding TTS function, handles errors using retries and GPT-based text correction, validates audio duration, and saves the output WAV file.
*   `core/_10_gen_audio.py`: Generates individual audio segments using the selected TTS backend via `tts_main.py`. Adjusts the speed of the generated audio using a computed factor (`ffmpeg`) to match target durations specified in the task file, and concatenates segments into chunks. Uses `ThreadPoolExecutor` for parallel processing.
*   `core/_11_merge_audio.py`: Merges the generated and speed-adjusted audio segments (`.wav` files from `output/audio_segments/`) into a single, continuous dubbed audio track (`output/dub.wav`), adding silences according to subtitle timings. Also generates a corresponding SRT file (`output/dub.srt`).
*   `core/_12_dub_to_vid.py`: The final synthesis step for dubbing. Merges the original video, the generated dubbed audio track (`output/dub.wav`), and the separated background music (`output/background.mp3`, if Demucs was used) using `ffmpeg`. Optionally burns subtitles during this process. Includes audio normalization.

**7. Core Utilities and Configuration (`core/utils`):**

*   `core/prompts.py`: Defines standardized prompt templates used to guide the LLM (GPT) for tasks such as sentence splitting, summarization, translation (fidelity/expressiveness), subtitle alignment, and text optimization/correction for TTS.
*   `core/utils/ask_gpt.py`: Provides a robust interface (`ask_gpt` function) for interacting with the OpenAI GPT models. Includes caching (file-based), JSON response repair (`json_repair`), response validation, error handling with retries (`@except_handler`), and logging.
*   `core/utils/config_utils.py`: Utility functions (`load_key`, `update_key`) for loading and updating configuration settings from `config.yaml` using `ruamel.yaml` (preserves formatting) and `threading.Lock` for thread-safe access. Includes `get_joiner` for language-specific text concatenation.
*   `core/utils/decorator.py`: Defines reusable decorators: `except_handler` for adding retry logic and error reporting to functions, and `check_file_exists` for skipping function execution if the output file already exists. Uses `rich` for formatted output.
*   `core/utils/delete_retry_dubbing.py`: Provides a function (`delete_dubbing_files`) to clean up specific intermediate files and directories associated with the dubbing process (e.g., `dub.wav`, `output_dub.mp4`, `output/audio/segs`).
*   `core/utils/onekeycleanup.py`: Implements a `cleanup` function to organize and archive files from the `output` directory into a structured `history` directory based on the video name. Includes filename sanitization and robust file moving/deletion logic.
*   `core/utils/pypi_autochoose.py`: A utility for automatically testing and selecting the fastest PyPI mirror and configuring pip to use it. Uses `rich` for UI.
*   `core/utils/models.py`: Defines constants representing filepaths of various intermediate and output files used throughout the pipeline.
*   `core/__init__.py`, `core/asr_backend/__init__.py`, `core/spacy_utils/__init__.py`, `core/st_utils/__init__.py`, `core/tts_backend/__init__.py`: Package initialization files, defining the public interfaces (`__all__`) for their respective packages/subpackages.
*   `core/__init__.py`: Initializes the main `core` package, exporting key functions and modules from subpackages for easier access.

**8. Batch Processing Module (`batch`):**

*   `batch/utils/settings_check.py`: Validates the settings defined in `batch/tasks_setting.xlsx` against the video files in `batch/input`, checking for file existence, valid URLs, and correct configuration values (e.g., dubbing flags). Uses `rich` for output.
*   `batch/utils/video_processor.py`: Defines the `process_video` function, which orchestrates the processing pipeline for *a single* video in a batch job. Handles input (URL or local file), calls the core processing steps (transcription, translation, subtitling, optional dubbing), manages retries, handles output folders, and invokes `cleanup`.
*   `batch/utils/batch_processor.py`: The main coordinator for batch processing. Reads tasks from `batch/tasks_setting.xlsx` (using `pandas`), iterates through the tasks, validates settings (`settings_check.py`), manages language configuration changes, calls `video_processor.py` for each video, handles errors and retries (including recovering files from the ERROR folder), and updates the status in the Excel file. Uses `rich` for console output.

**9. Streamlit Interface Module (`core/st_utils`, `st.py`):**

*   `core/st_utils/download_video_section.py`: Implements the Streamlit UI section for selecting the input video, allowing users to download from YouTube (using `core/_1_ytdlp.py`) or upload local files (video or audio, with audio-to-video conversion using `ffmpeg`).
*   `core/st_utils/sidebar_setting.py`: Creates the configuration sidebar in the Streamlit UI. Allows users to set the display language, LLM parameters (API keys, model, base URL), subtitle settings (source/target languages, Demucs toggle, burning toggle), and dubbing settings (TTS method and related parameters such as voice, API key). Loads/saves settings using `core/utils/config_utils.py` and triggers `st.rerun()` on changes. Includes API key validation.
*   `core/st_utils/imports_and_utils.py`: Contains common imports and utility functions for the Streamlit application, such as functions for creating download buttons for zipped subtitle files and CSS styling for buttons.
*   `st.py`: The main entry point for the Streamlit web application. Sets up the page configuration, displays the logo, creates the sidebar using `sidebar_setting.py`, manages the main UI sections (video downloading/uploading via `download_video_section.py`, text processing, audio processing), and triggers the core processing functions (`process_text`, `process_audio`) based on user interaction (button clicks). Uses `st.spinner` to indicate progress during long-running operations.

**10. Internationalization Module (`translations`):**

*   `translations/translations.py`: Implements UI translation functionality. Defines supported display languages, loads translated strings from JSON files based on the selected language (`load_key("display_language")`), and provides a `translate(key)` function to retrieve translated text, falling back to the original key if a translation is missing.

Videolingo automates the complete process from video acquisition to the final generation of videos with translated subtitles and dubbing.  The enhanced modular design allows each step to be more easily run and debugged, provides greater flexibility through multiple backend options (ASR, TTS), and offers improved configuration management and user interfaces for both interactive and batch processing workflows.