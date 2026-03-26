import streamlit as st
import os, sys
from core.st_utils.imports_and_utils import *
from core import *
from core.dubbing_backend.camb_dubbing import camb_dub, CAMB_LANGUAGE_IDS

# SET PATH
current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ['PATH'] += os.pathsep + current_dir
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(page_title="VideoLingo", page_icon="docs/logo.svg")

SUB_VIDEO = "output/output_sub.mp4"
DUB_VIDEO = "output/output_dub.mp4"

def text_processing_section():
    st.header(t("b. Translate and Generate Subtitles"))
    with st.container(border=True):
        st.markdown(f"""
        <p style='font-size: 20px;'>
        {t("This stage includes the following steps:")}
        <p style='font-size: 20px;'>
            1. {t("WhisperX word-level transcription")}<br>
            2. {t("Sentence segmentation using NLP and LLM")}<br>
            3. {t("Summarization and multi-step translation")}<br>
            4. {t("Cutting and aligning long subtitles")}<br>
            5. {t("Generating timeline and subtitles")}<br>
            6. {t("Merging subtitles into the video")}
        """, unsafe_allow_html=True)

        if not os.path.exists(SUB_VIDEO):
            if st.button(t("Start Processing Subtitles"), key="text_processing_button"):
                process_text()
                st.rerun()
        else:
            if load_key("burn_subtitles"):
                st.video(SUB_VIDEO)
            download_subtitle_zip_button(text=t("Download All Srt Files"))
            
            if st.button(t("Archive to 'history'"), key="cleanup_in_text_processing"):
                cleanup()
                st.rerun()
            return True

def process_text():
    with st.spinner(t("Using Whisper for transcription...")):
        _2_asr.transcribe()
    with st.spinner(t("Splitting long sentences...")):  
        _3_1_split_nlp.split_by_spacy()
        _3_2_split_meaning.split_sentences_by_meaning()
    with st.spinner(t("Summarizing and translating...")):
        _4_1_summarize.get_summary()
        if load_key("pause_before_translate"):
            input(t("⚠️ PAUSE_BEFORE_TRANSLATE. Go to `output/log/terminology.json` to edit terminology. Then press ENTER to continue..."))
        _4_2_translate.translate_all()
    with st.spinner(t("Processing and aligning subtitles...")): 
        _5_split_sub.split_for_sub_main()
        _6_gen_sub.align_timestamp_main()
    with st.spinner(t("Merging subtitles to video...")):
        _7_sub_into_vid.merge_subtitles_to_video()
    
    st.success(t("Subtitle processing complete! 🎉"))
    st.balloons()

def audio_processing_section():
    st.header(t("c. Dubbing"))
    with st.container(border=True):
        st.markdown(f"""
        <p style='font-size: 20px;'>
        {t("This stage includes the following steps:")}
        <p style='font-size: 20px;'>
            1. {t("Generate audio tasks and chunks")}<br>
            2. {t("Extract reference audio")}<br>
            3. {t("Generate and merge audio files")}<br>
            4. {t("Merge final audio into video")}
        """, unsafe_allow_html=True)
        if not os.path.exists(DUB_VIDEO):
            if st.button(t("Start Audio Processing"), key="audio_processing_button"):
                process_audio()
                st.rerun()
        else:
            st.success(t("Audio processing is complete! You can check the audio files in the `output` folder."))
            if load_key("burn_subtitles"):
                st.video(DUB_VIDEO) 
            if st.button(t("Delete dubbing files"), key="delete_dubbing_files"):
                delete_dubbing_files()
                st.rerun()
            if st.button(t("Archive to 'history'"), key="cleanup_in_audio_processing"):
                cleanup()
                st.rerun()

def process_audio():
    with st.spinner(t("Generate audio tasks")): 
        _8_1_audio_task.gen_audio_task_main()
        _8_2_dub_chunks.gen_dub_chunks()
    with st.spinner(t("Extract refer audio")):
        _9_refer_audio.extract_refer_audio_main()
    with st.spinner(t("Generate all audio")):
        _10_gen_audio.gen_audio()
    with st.spinner(t("Merge full audio")):
        _11_merge_audio.merge_full_audio()
    with st.spinner(t("Merge dubbing to the video")):
        _12_dub_to_vid.merge_video_audio()
    
    st.success(t("Audio processing complete! 🎇"))
    st.balloons()

def camb_dubbing_section():
    st.markdown(f"<p style='font-size: 20px;'>{t('Dub your video in one step using CAMB AI. Handles transcription, translation, and dubbing automatically.')}</p>", unsafe_allow_html=True)

    camb_dub_output = "output/output_camb_dub.mp4"

    # API key
    api_key = st.text_input("CAMB AI API Key", value=load_key("camb_dubbing.api_key"), key="camb_dub_api_key")
    if api_key != load_key("camb_dubbing.api_key"):
        update_key("camb_dubbing.api_key", api_key)

    if not os.path.exists(camb_dub_output):
        video_url = st.text_input(t("Video URL (YouTube, Google Drive, or direct link)"), key="camb_dub_url")

        lang_names = list(CAMB_LANGUAGE_IDS.keys())
        c1, c2 = st.columns(2)
        with c1:
            source_lang = st.selectbox(t("Source Language"), options=lang_names, index=0, key="camb_dub_source_main")
        with c2:
            target_lang = st.selectbox(t("Target Language"), options=lang_names, index=1, key="camb_dub_target_main")

        if st.button(t("Start CAMB Dubbing"), key="camb_dubbing_button"):
            if not video_url:
                st.error(t("Please enter a video URL"))
                return
            source_id = CAMB_LANGUAGE_IDS[source_lang]
            target_id = CAMB_LANGUAGE_IDS[target_lang]
            with st.spinner(t("CAMB AI is dubbing your video... This may take several minutes.")):
                try:
                    camb_dub(video_url, source_id, [target_id], camb_dub_output)
                    st.success(t("CAMB dubbing complete!"))
                    st.rerun()
                except Exception as e:
                    st.error(f"CAMB dubbing failed: {e}")
    else:
        st.success(t("CAMB AI dubbing is complete!"))
        st.video(camb_dub_output)
        if st.button(t("Delete CAMB dubbed video"), key="delete_camb_dub"):
            os.remove(camb_dub_output)
            st.rerun()

def main():
    logo_col, _ = st.columns([1,1])
    with logo_col:
        st.image("docs/logo.png", width="stretch")
    st.markdown(button_style, unsafe_allow_html=True)
    welcome_text = t("Hello, welcome to VideoLingo. If you encounter any issues, feel free to get instant answers with our Free QA Agent <a href=\"https://share.fastgpt.in/chat/share?shareId=066w11n3r9aq6879r4z0v9rh\" target=\"_blank\">here</a>! You can also try out our SaaS website at <a href=\"https://videolingo.io\" target=\"_blank\">videolingo.io</a> for free!")
    st.markdown(f"<p style='font-size: 20px; color: #808080;'>{welcome_text}</p>", unsafe_allow_html=True)
    # add settings
    with st.sidebar:
        page_setting()
        st.markdown(give_star_button, unsafe_allow_html=True)

    tab_videolingo, tab_camb = st.tabs([t("VideoLingo Pipeline"), t("CAMB AI Dubbing")])

    with tab_videolingo:
        download_video_section()
        text_processing_section()
        audio_processing_section()

    with tab_camb:
        camb_dubbing_section()

if __name__ == "__main__":
    main()
