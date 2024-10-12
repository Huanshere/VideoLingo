import streamlit as st
import os, sys
from st_components.imports_and_utils import *
from core.config_utils import load_key

# SET PATH
current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ['PATH'] += os.pathsep + current_dir
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(page_title="VideoLingo", page_icon="st_components/icon.png")

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

        if not os.path.exists("output/output_video_with_subs.mp4"):
            if st.button("Start Processing Subtitles", key="text_processing_button"):
                process_text()
                st.rerun()
        else:
            st.success("Subtitle translation is complete! It's recommended to download the srt file and process it yourself.")
            if load_key("resolution") != "0x0":
                st.video("output/output_video_with_subs.mp4")
            download_subtitle_zip_button(text="Download All Subtitles")
            
            if st.button("Archive to 'history'", key="cleanup_in_text_processing"):
                cleanup()
                st.rerun()
            return True

def process_text():
    with st.spinner("Using Whisper for transcription..."):
        step2_whisper.transcribe()
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
    st.header("Dubbing (beta)")
    with st.container(border=True):
        st.markdown("""
        <p style='font-size: 20px;'>
        This stage includes the following steps:
        <p style='font-size: 20px;'>
            1. Generate audio tasks<br>
            2. UVR5 Process<br>
            3. Generate audio<br>
            4. Merge audio into the video
        """, unsafe_allow_html=True)
        if not os.path.exists("output/output_video_with_audio.mp4"):
            if st.button("Start Audio Processing", key="audio_processing_button"):
                process_audio()
                st.rerun()
        else:
            st.success("Audio processing is complete! You can check the audio files in the `output` folder.")
            if load_key("resolution") != "0x0": 
                st.video("output/output_video_with_audio.mp4") 
            if st.button("Delete dubbing files", key="delete_dubbing_files"):
                delete_dubbing_files()
                st.rerun()
            if st.button("Archive to 'history'", key="cleanup_in_audio_processing"):
                cleanup()
                st.rerun()

def process_audio():
    with st.spinner("Generate audio tasks"): 
        step8_gen_audio_task.gen_audio_task_main()
    with st.spinner("UVR5 Process"):
        step9_uvr_audio.uvr_audio_main()
    with st.spinner("Generate audio"):
        step10_gen_audio.process_sovits_tasks()
    with st.spinner("Merge audio into the video"):
        step11_merge_audio_to_vid.merge_main()
    
    st.success("Audio processing complete! 🎇")
    st.balloons()

def main():
    
    st.markdown(button_style, unsafe_allow_html=True)

    st.markdown("<h1 style='font-size: 3rem;'>VideoLingo: Connecting Every Frame Across the World</h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 20px; color: #808080;'>Hello, thank you for visiting VideoLingo. This project is currently under construction. If you encounter any issues, please feel free to ask questions on Github! You can also visit our website: videolingo.io</p>", unsafe_allow_html=True)
    # add settings
    with st.sidebar:
        page_setting()
        st.markdown(give_star_button, unsafe_allow_html=True)
    download_video_section()
    text_processing_section()
    audio_processing_section()

if __name__ == "__main__":
    main()
