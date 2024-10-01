import streamlit as st
import os, sys
from st_components.imports_and_utils import *

current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ['PATH'] += os.pathsep + current_dir
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(page_title="VideoLingo", page_icon="st_components/icon.png")

def text_processing_section():
    st.header(gls("translate_generate_subtitle"))
    with st.container(border=True):
        st.markdown(f"""
        <p style='font-size: 20px;'>
        {gls("text_processing_steps")}
        <p style='font-size: 20px;'>
            {gls("step1")}<br>
            {gls("step2")}<br>
            {gls("step3")}<br>
            {gls("step4")}<br>
            {gls("step5")}<br>
            {gls("step6")}
        """, unsafe_allow_html=True)

        if not os.path.exists("output/output_video_with_subs.mp4"):
            if st.button(gls("start_processing_subtitles"), key="text_processing_button"):
                with st.spinner(gls("processing_subtitles")):
                    process_text()
                st.success(gls("subtitle_processing_complete"))
                st.balloons()
                st.rerun()
        else:
            #! ffmpeg has problems merging subtitles on linux
            if sys.platform.startswith('linux'):
                st.warning(gls("linux_warning"))
            else:
                st.success(gls("subtitle_translation_complete"))
            from config import RESOLUTION
            if RESOLUTION != "0x0":
                st.video("output/output_video_with_subs.mp4")
            download_subtitle_zip_button(text=gls("download_all_subtitles"))
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(gls("archive_to_history"), key="cleanup_in_text_processing"):
                    cleanup()
                    st.rerun()
            with col2:
                if st.button(gls("start_over"), key="start_over_text_processing"):
                    delete_output_files()
                    st.rerun()
            return True

def process_text():
    video_file = step1_ytdlp.find_video_files()
    
    progress_bar = st.progress(0)
    total_steps = 6
    
    video_file = step1_ytdlp.find_video_files()
    progress_bar.progress(1/total_steps)
    
    with st.spinner(gls("using_whisper_transcription")):
        step2_whisper.transcribe(video_file)
    progress_bar.progress(2/total_steps)
    
    with st.spinner(gls("splitting_long_sentences")):  
        step3_1_spacy_split.split_by_spacy()
        step3_2_splitbymeaning.split_sentences_by_meaning()
    progress_bar.progress(3/total_steps)
    
    with st.spinner(gls("summarizing_and_translating")):
        step4_1_summarize.get_summary()
        from config import PAUSE_BEFORE_TRANSLATE
        if PAUSE_BEFORE_TRANSLATE:
            input("⚠️ PAUSE_BEFORE_TRANSLATE. Go to `output/log/terminology.json` to edit terminology. Then press ENTER to continue...")
        step4_2_translate_all.translate_all()
    progress_bar.progress(4/total_steps)
    
    with st.spinner(gls("processing_aligning_subtitles")): 
        step5_splitforsub.split_for_sub_main()
        step6_generate_final_timeline.align_timestamp_main()
    progress_bar.progress(5/total_steps)
    
    with st.spinner(gls("merging_subtitles_to_video")):
        step7_merge_sub_to_vid.merge_subtitles_to_video()
    progress_bar.progress(6/total_steps)
    
    st.success(gls("subtitle_processing_complete"))
    st.balloons()

def audio_processing_section():
    st.header(gls("audio_dubbing_title"))
    with st.container(border=True):
        st.markdown(f"""
        <p style='font-size: 20px;'>
        {gls("audio_processing_steps")}
        <p style='font-size: 20px;'>
            {gls("audio_step1")}<br>
            {gls("audio_step2")}<br>
            {gls("audio_step3")}<br>
            {gls("audio_step4")}
        """, unsafe_allow_html=True)
        if not os.path.exists("output/output_video_with_audio.mp4"):
            if st.button(gls("start_audio_processing"), key="audio_processing_button"):
                with st.spinner(gls("processing_audio")):
                    process_audio()
                st.success(gls("audio_processing_complete"))
                st.balloons()
                st.rerun()
        else:
            st.success(gls("audio_processing_complete"))
            from config import RESOLUTION
            if RESOLUTION != "0x0": 
                st.video("output/output_video_with_audio.mp4") 
            if st.button(gls("delete_dubbing_files"), key="delete_dubbing_files"):
                delete_dubbing_files()
                st.rerun()
            if st.button(gls("archive_to_history"), key="cleanup_in_audio_processing"):
                cleanup()
                st.rerun()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(gls("delete_dubbing_files"), key="delete_dubbing_files"):
                    delete_dubbing_files()
                    st.rerun()
            with col2:
                if st.button(gls("archive_to_history"), key="cleanup_in_audio_processing"):
                    cleanup()
                    st.rerun()
            with col3:
                if st.button(gls("start_over"), key="start_over_audio_processing"):
                    delete_output_files()
                    st.rerun()

def process_audio():
    with st.spinner(gls("audio_step1").split(".")[1]): 
        step8_gen_audio_task.gen_audio_task_main()
    progress_bar = st.progress(0)
    total_steps = 4
    
    step8_gen_audio_task.gen_audio_task_main()
    progress_bar.progress(1/total_steps)
    
    with st.spinner(gls("audio_step2").split(".")[1]):
        step9_uvr_audio.uvr_audio_main()
    progress_bar.progress(2/total_steps)
    
    with st.spinner(gls("audio_step3").split(".")[1]):
        step10_gen_audio.process_sovits_tasks()
    progress_bar.progress(3/total_steps)
    
    with st.spinner(gls("audio_step4").split(".")[1]):
        step11_merge_audio_to_vid.merge_main()
    progress_bar.progress(4/total_steps)
    
    st.success(gls("audio_processing_complete_emoji"))
    st.balloons()

def delete_output_files():
    output_files = [
        "output/output_video_with_subs.mp4",
        "output/output_video_with_audio.mp4"
    ]
    for file in output_files:
        if os.path.exists(file):
            os.remove(file)
    st.success(gls("output_files_deleted"))

def main():
    
    st.markdown(button_style, unsafe_allow_html=True)

    st.markdown(f"<h1 style='font-size: 3rem;'>{gls('app_title')}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size: 20px; color: #808080;'>{gls('app_description')}</p>", unsafe_allow_html=True)
    # add settings
    with st.sidebar:
        page_setting()
        st.markdown(give_star_button, unsafe_allow_html=True)
    download_video_section()
    text_processing_section()
    audio_processing_section()

if __name__ == "__main__":
    main()
