import streamlit as st
import os, sys
from st_components.imports_and_utils import *
from core.config_utils import load_key

# 設置路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ['PATH'] += os.pathsep + current_dir
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(page_title="VideoLingo", page_icon="docs/logo.svg")

SUB_VIDEO = "output/output_sub.mp4"
DUB_VIDEO = "output/output_dub.mp4"

def text_processing_section():
    st.header("翻譯和生成字幕")
    with st.container(border=True):
        st.markdown("""
        <p style='font-size: 20px;'>
        此階段包含以下步驟：
        <p style='font-size: 20px;'>
            1. WhisperX 逐字轉錄<br>
            2. 使用 NLP 和 LLM 進行句子分割<br>
            3. 總結和多步翻譯<br>
            4. 切割和對齊長字幕<br>
            5. 生成時間軸和字幕<br>
            6. 將字幕合併到影片中
        """, unsafe_allow_html=True)

        if not os.path.exists(SUB_VIDEO):
            if st.button("開始處理字幕", key="text_processing_button"):
                process_text()
                st.rerun()
        else:
            if load_key("resolution") != "0x0":
                st.video(SUB_VIDEO)
            download_subtitle_zip_button(text="下載所有字幕")
            
            if st.button("歸檔到'歷史記錄'", key="cleanup_in_text_processing"):
                cleanup()
                st.rerun()
            return True

def process_text():
    with st.spinner("使用 Whisper 進行轉錄中..."):
        step2_whisperX.transcribe()
    with st.spinner("分割長句中..."):  
        step3_1_spacy_split.split_by_spacy()
        step3_2_splitbymeaning.split_sentences_by_meaning()
    with st.spinner("總結和翻譯中..."):
        step4_1_summarize.get_summary()
        if load_key("pause_before_translate"):
            input("⚠️ 翻譯前暫停。請前往 `output/log/terminology.json` 編輯術語。完成後按回車繼續...")
        step4_2_translate_all.translate_all()
    with st.spinner("處理和對齊字幕中..."): 
        step5_splitforsub.split_for_sub_main()
        step6_generate_final_timeline.align_timestamp_main()
    with st.spinner("將字幕合併到影片中..."):
        step7_merge_sub_to_vid.merge_subtitles_to_video()
    
    st.success("字幕處理完成！🎉")
    st.balloons()

def audio_processing_section():
    st.header("配音")
    with st.container(border=True):
        st.markdown("""
        <p style='font-size: 20px;'>
        此階段包含以下步驟：
        <p style='font-size: 20px;'>
            1. 生成音訊任務和分段<br>
            2. 提取參考音訊<br>
            3. 生成和合併音訊文件<br>
            4. 將最終音訊合併到影片中
        """, unsafe_allow_html=True)
        if not os.path.exists(DUB_VIDEO):
            if st.button("開始處理音訊", key="audio_processing_button"):
                process_audio()
                st.rerun()
        else:
            st.success("音訊處理完成！你可以在 `output` 文件夾中查看音訊文件。")
            if load_key("resolution") != "0x0": 
                st.video(DUB_VIDEO) 
            if st.button("刪除配音文件", key="delete_dubbing_files"):
                delete_dubbing_files()
                st.rerun()
            if st.button("歸檔到'歷史記錄'", key="cleanup_in_audio_processing"):
                cleanup()
                st.rerun()

def process_audio():
    with st.spinner("生成音訊任務中"): 
        step8_1_gen_audio_task.gen_audio_task_main()
        step8_2_gen_dub_chunks.gen_dub_chunks()
    with st.spinner("提取參考音訊中"):
        step9_extract_refer_audio.extract_refer_audio_main()
    with st.spinner("生成所有音訊中"):
        step10_gen_audio.gen_audio()
    with st.spinner("合併完整音訊中"):
        step11_merge_full_audio.merge_full_audio()
    with st.spinner("將配音合併到影片中"):
        step12_merge_dub_to_vid.merge_video_audio()
    
    st.success("音訊處理完成！🎇")
    st.balloons()

def main():
    logo_col, _ = st.columns([1,1])
    with logo_col:
        st.image("docs/logo.png", use_column_width=True)
    st.markdown(button_style, unsafe_allow_html=True)
    st.markdown("<p style='font-size: 20px; color: #808080;'>你好，歡迎使用 VideoLingo。本項目目前正在建設中。如果遇到任何問題，請隨時在 Github 上提問！現在可以在我們的官網免費體驗：<a href='https://videolingo.io' target='_blank'>videolingo.io</a></p>", unsafe_allow_html=True)
    # add settings
    with st.sidebar:
        page_setting()
        st.markdown(give_star_button, unsafe_allow_html=True)
    download_video_section()
    text_processing_section()
    audio_processing_section()

if __name__ == "__main__":
    main()
