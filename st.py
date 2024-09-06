import streamlit as st
import os, sys
from st_components.imports_and_utils import *
from st_components.download_video_section import download_video_section
from st_components.sidebar_setting import page_setting

current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ['PATH'] += os.pathsep + current_dir

cloud = 1 if sys.platform.startswith('linux') else 0

def text_processing_section():
    st.header("翻译并生成字幕")
    with st.container(border=True):
        st.markdown("""
        <p style='font-size: 20px;'>
        该阶段包括以下步骤：
        <p style='font-size: 20px;'>
            1. Whisper 单词级转录<br>
            2. Spacy 和 Claude 分割句子<br>
            3. 总结和多步翻译<br>
            4. 切割对齐长字幕<br>
            5. 生成时间轴和字幕<br>
            6. 将字幕合并到视频中
        """, unsafe_allow_html=True)

        if not os.path.exists("output/output_video_with_subs.mp4"):
            if st.button(" 开始处理字幕 ", key="text_processing_button"):
                process_text()
                st.rerun()
        else:
            if cloud:
                st.warning("目前 Linux 下合并中文字幕展示乱码，请下载 srt 文件自行压制处理～")
            else:
                st.success("字幕翻译已完成! 建议下载 srt 文件自行压制 ~")
            st.video("output/output_video_with_subs.mp4")
            download_subtitle_zip_button(text="下载所有字幕")
            
            if st.button("归档到`history`文件夹", key="cleanup_in_text_processing"):
                cleanup()
                st.rerun()
            return True

def process_text():
    video_file = step1_ytdlp.find_video_files()
    
    with st.spinner("使用Whisper进行转录..."):
        step2_whisper_stamped.transcribe(video_file)
    with st.spinner("分割长句..."):  
        step3_1_spacy_split.split_by_spacy()
        step3_2_splitbymeaning.split_sentences_by_meaning()
    with st.spinner("总结和翻译..."):
        step4_1_summarize.get_summary()
        step4_2_translate_all.translate_all()
    with st.spinner("处理对齐字幕..."): 
        step5_splitforsub.split_for_sub_main()
        step6_generate_final_timeline.align_timestamp_main()
    with st.spinner("合并字幕到视频..."):
        step7_merge_sub_to_vid.merge_subtitles_to_video()
    
    st.success("字幕处理完成! 🎉")
    st.balloons()

def audio_processing_section():
    st.header("GPT-SoVits 配音(beta 开发完善中)")
    with st.container(border=True):
        st.markdown("""
        <p style='font-size: 20px;'>
        该阶段包括以下步骤：
        <p style='font-size: 20px;'>
            1. 提取参考音频<br>
            2. 生成音频任务<br>
            3. 使用SoVITS生成音频<br>
            4. 将音频合并到视频中
        """, unsafe_allow_html=True)
        if not os.path.exists("output/output_video_with_audio.mp4"):
            if st.button("开始配音处理", key="audio_processing_button"):
                process_audio()
                st.video("output/output_video_with_audio.mp4")
                return True
        else:
            st.success("配音处理已完成! 可以在`output`文件夹下查看音频文件 ~")
            st.video("output/output_video_with_audio.mp4") 
            if st.button("归档到`history`文件夹", key="cleanup_in_audio_processing"):
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
    st.set_page_config(page_title="VideoLingo: 连接世界的每一帧", page_icon="🌉")
    st.markdown(button_style, unsafe_allow_html=True)

    st.markdown("<h1 style='font-size: 3rem;'>VideoLingo: 连接世界的每一帧</h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 20px; color: #808080;'>哈喽，感谢访问 VideoLingo. 目前该项目还在建设中，遇到任何问题可以在 Github 或 QQ 群提问！我们将在不久的未来呈现更多功能，感谢理解！</p>", unsafe_allow_html=True)
    # 在侧边栏添加设置部分
    with st.sidebar:
        page_setting()
        st.markdown(give_star_button, unsafe_allow_html=True)
    download_video_section(cloud)
    text_processing_section()
    st.warning("配音功能仍在开发中，暂已停用，感谢理解！")
    # if not cloud:
    #     audio_processing_section()

if __name__ == "__main__":
    main()