import streamlit as st
import os, sys
from st_components.imports_and_utils import *
from st_components.download_video_section import download_video_section
from st_components.sidebar_setting import page_setting
from st_components.i18n import get_localized_string as gls

current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ['PATH'] += os.pathsep + current_dir
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if_linux = 1 if sys.platform.startswith('linux') else 0
st.set_page_config(page_title="VideoLingo", page_icon="🌉")

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
                process_text()
                st.rerun()
        else:
            if if_linux:
                st.warning(gls("linux_warning"))
            else:
                st.success(gls("subtitle_translation_complete"))
            from config import RESOLUTION
            if RESOLUTION != "0x0":
                st.video("output/output_video_with_subs.mp4")
            download_subtitle_zip_button(text=gls("download_all_subtitles"))
            
            if st.button(gls("archive_to_history"), key="cleanup_in_text_processing"):
                cleanup()
                st.rerun()
            return True

def process_text():
    video_file = step1_ytdlp.find_video_files()
    
    with st.spinner(gls("using_whisper_transcription")):
        step2_whisper.transcribe(video_file)
    with st.spinner(gls("splitting_long_sentences")):  
        step3_1_spacy_split.split_by_spacy()
        step3_2_splitbymeaning.split_sentences_by_meaning()
    with st.spinner(gls("summarizing_and_translating")):
        step4_1_summarize.get_summary()
        step4_2_translate_all.translate_all()
    with st.spinner(gls("processing_aligning_subtitles")): 
        step5_splitforsub.split_for_sub_main()
        step6_generate_final_timeline.align_timestamp_main()
    with st.spinner(gls("merging_subtitles_to_video")):
        step7_merge_sub_to_vid.merge_subtitles_to_video()
    
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
                process_audio()
                st.video("output/output_video_with_audio.mp4")
                return True
        else:
            st.success(gls("audio_processing_complete"))
            st.video("output/output_video_with_audio.mp4") 
            if st.button(gls("archive_to_history"), key="cleanup_in_audio_processing"):
                cleanup()
                st.rerun()

def process_audio():
    input_video = step1_ytdlp.find_video_files()
    
    with st.spinner("提取音频..."): 
        step8_extract_refer_audio.step8_main(input_video)
    with st.spinner("生成音频任务..."):
        step9_generate_audio_task.step9_main()
    with st.spinner("使用SoVITS生成音频...\n⚠️ 如果这一步因字幕出错，请根据cmd提示修改对应字幕后重新运行"):
        step10_generate_audio.process_sovits_tasks()
    with st.spinner("合并音频到视频..."):
        step11_merge_audio_to_vid.merge_main()
    
    st.success("音频处理完成! 🎉")
    st.balloons()

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
    st.warning(gls("dubbing_feature_warning"))
    # if not if_linux:
    #     audio_processing_section()

if __name__ == "__main__":
    main()