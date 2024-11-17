import streamlit as st
import os, sys
from st_components.imports_and_utils import *
from core.config_utils import load_key

# SET PATH
current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ['PATH'] += os.pathsep + current_dir
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(page_title="VideoLingo", page_icon="docs/logo.svg")

SUB_VIDEO = "output/output_sub.mp4"
DUB_VIDEO = "output/output_dub.mp4"

def text_processing_section():
    st.header("Translate and Generate Subtitles")
    with st.container(border=True):
        st.markdown("""
        <p style='font-size: 20px;'>
        This stage includes the following steps:
        <p style='font-size: 20px;'>
            1. WhisperX word-level transcription<br>
            2. Sentence segmentation using NLP and LLM<br>
            3. Summarization and multi-step translation<br>
            4. Cutting and aligning long subtitles<br>
            5. Generating timeline and subtitles<br>
            6. Merging subtitles into the video
        """, unsafe_allow_html=True)

        if not os.path.exists(SUB_VIDEO):
            if st.button("Start Processing Subtitles", key="text_processing_button"):
                process_text()
                st.rerun()
        else:
            if load_key("resolution") != "0x0":
                st.video(SUB_VIDEO)
            download_subtitle_zip_button(text="Download All Srt Files")
            
            if st.button("Archive to 'history'", key="cleanup_in_text_processing"):
                cleanup()
                st.rerun()
            return True

def process_text():
    with st.spinner("Using Whisper for transcription..."):
        step2_whisperX.transcribe()
    with st.spinner("Splitting long sentences..."):  
        step3_1_spacy_split.split_by_spacy()
        step3_2_splitbymeaning.split_sentences_by_meaning()
    with st.spinner("Summarizing and translating..."):
        step4_1_summarize.get_summary()
        if load_key("pause_before_translate"):
            input("⚠️ PAUSE_BEFORE_TRANSLATE. Go to `output/log/terminology.json` to edit terminology. Then press ENTER to continue...")
        step4_2_translate_all.translate_all()
    with st.spinner("Processing and aligning subtitles..."): 
        step5_splitforsub.split_for_sub_main()
        step6_generate_final_timeline.align_timestamp_main()
    with st.spinner("Merging subtitles to video..."):
        step7_merge_sub_to_vid.merge_subtitles_to_video()
    
    st.success("Subtitle processing complete! 🎉")
    st.balloons()

def audio_processing_section():
    st.header("Dubbing")
    with st.container(border=True):
        st.markdown("""
        <p style='font-size: 20px;'>
        This stage includes the following steps:
        <p style='font-size: 20px;'>
            1. Generate audio tasks and chunks<br>
            2. Extract reference audio<br>
            3. Generate and merge audio files<br>
            4. Merge final audio into video
        """, unsafe_allow_html=True)
        if not os.path.exists(DUB_VIDEO):
            if st.button("Start Audio Processing", key="audio_processing_button"):
                process_audio()
                st.rerun()
        else:
            st.success("Audio processing is complete! You can check the audio files in the `output` folder.")
            if load_key("resolution") != "0x0": 
                st.video(DUB_VIDEO) 
            if st.button("Delete dubbing files", key="delete_dubbing_files"):
                delete_dubbing_files()
                st.rerun()
            if st.button("Archive to 'history'", key="cleanup_in_audio_processing"):
                cleanup()
                st.rerun()

def process_audio():
    with st.spinner("Generate audio tasks"): 
        step8_1_gen_audio_task.gen_audio_task_main()
        step8_2_gen_dub_chunks.gen_dub_chunks()
    with st.spinner("Extract refer audio"):
        step9_extract_refer_audio.extract_refer_audio_main()
    with st.spinner("Generate all audio"):
        step10_gen_audio.gen_audio()
    with st.spinner("Merge full audio"):
        step11_merge_full_audio.merge_full_audio()
    with st.spinner("Merge dubbing to the video"):
        step12_merge_dub_to_vid.merge_video_audio()
    
    st.success("Audio processing complete! 🎇")
    st.balloons()

def main():
    logo_col, _ = st.columns([1,1])
    with logo_col:
        st.image("docs/logo.png", use_column_width=True)
    st.markdown(button_style, unsafe_allow_html=True)
    st.markdown("<p style='font-size: 20px; color: #808080;'>Hello, welcome to VideoLingo. This project is currently under construction. If you encounter any issues, please feel free to ask questions on Github! You can also use VideoLingo on our website now: <a href='https://videolingo.io' target='_blank'>videolingo.io</a></p>", unsafe_allow_html=True)
    # add settings
    with st.sidebar:
        page_setting()
        st.markdown(give_star_button, unsafe_allow_html=True)
    download_video_section()
    text_processing_section()
    audio_processing_section()

if __name__ == "__main__":
    main()
