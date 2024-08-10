import streamlit as st
import os, glob
from core import step1_ytdlp, step2_whisper_stamped, step3_1_spacy_split, step3_2_splitbymeaning
from core import step4_1_summarize, step4_2_translate_all, step5_splitforsub, step6_generate_final_timeline
from core import step7_merge_sub_to_vid, step8_extract_refer_audio, step9_generate_audio_task
from core import step10_generate_audio, step11_merge_audio_to_vid
from core.onekeycleanup import cleanup

def set_page_config():
    st.set_page_config(
        page_title="VideoLingo: 连接世界的每一帧",
        page_icon="🌉",
        layout="wide",
        initial_sidebar_state="expanded",
    )

def sidebar_info():
    st.sidebar.title("🌟 关于 VideoLingo")
    st.sidebar.info(
        "VideoLingo 是一个全自动烤肉机，"
        "可以下载视频、转录音频、翻译内容、"
        "生成专业级字幕，并进行个性化配音。"
    )
    st.sidebar.markdown("🚀 [看看 GitHub 仓库](https://github.com/Huanshere/VideoLingo) 🌟")
    st.sidebar.success("开始你的视频本地化之旅吧！")
    st.sidebar.markdown("### 📂 处理日志位于 `output` 文件夹")
    

    if st.sidebar.button("📦 一键归档历史记录", key="cleanup_button"):
        cleanup()

def create_step_progress(total_steps):
    progress_bar = st.progress(0)
    step_status = st.empty()
    return progress_bar, step_status

def update_progress(progress_bar, step_status, step, total_steps, description):
    progress = int(step / total_steps * 100)
    progress_bar.progress(progress)
    step_status.markdown(f"**步骤 {step}/{total_steps}**: {description}")

def download_video_section():
    st.header("1. 下载ytb 📥 或 上传本地视频 ⏫")
    with st.expander("展开详情", expanded=True):
        # st.info("这一步将从链接下载指定的YouTube视频或上传本地视频文件")
        
        if not glob.glob("*.mp4") + glob.glob("*.webm"):
            st.warning("请输入ytb链接 或 上传视频文件")

            url = st.text_input("输入YouTube视频链接:")
            if st.button("下载视频", key="download_button"):
                if url:
                    with st.spinner("正在下载视频..."):
                        step1_ytdlp.download_video_ytdlp(url, save_path='./')
                    st.success("视频下载成功! 🎉")
                    video_file = (glob.glob("*.mp4") + glob.glob("*.webm"))[0]
                    st.video(video_file)
                    return True
            
            st.write("或者")
            
            uploaded_file = st.file_uploader("上传视频文件", type=["mp4", "webm"])
            if uploaded_file:
                with open(os.path.join("./", uploaded_file.name), "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success("视频上传成功! 🎉")
                st.video(uploaded_file)
                st.rerun()  # 刷新

            if not url and not uploaded_file:
                return False
        else:
            st.success("视频文件已存在 ✅")
            video_file = (glob.glob("*.mp4") + glob.glob("*.webm"))[0]
            st.video(video_file)
            return True
    
    return False

def text_processing_section(progress_bar, step_status, total_steps):
    st.header("2-7. 文本处理 📝")
    with st.expander("展开详情", expanded=True):
        st.info("""
        这个阶段包括以下步骤：

        2. 使用Whisper进行语音转录
        3. 分割句子
        4. 总结和翻译内容
        5. 处理字幕
        6. 生成最终时间线
        7. 将字幕合并到视频中
                
        👀 输出请在命令行查看
        """)
        if not os.path.exists("output/output_video_with_subs.mp4"):
            if st.button("开始文本处理", key="text_processing_button"):
                process_text(progress_bar, step_status, total_steps)
                st.video("output/output_video_with_subs.mp4") # 展示处理后的视频
                return True
        else:
            update_progress(progress_bar, step_status, 7, total_steps, "字幕合并到视频完成")
            st.success("文本处理已完成! 🎉")
            st.video("output/output_video_with_subs.mp4") # 展示处理后的视频
            return True
    return False

def process_text(progress_bar, step_status, total_steps):
    video_file = (glob.glob("*.mp4") + glob.glob("*.webm"))[0]
    
    steps = [
        ("使用Whisper进行转录...", lambda: step2_whisper_stamped.transcript(video_file), 2),
        ("分割句子...", lambda: (step3_1_spacy_split.split_by_spacy(), step3_2_splitbymeaning.split_sentences_by_meaning()), 3),
        ("总结和翻译...", lambda: (step4_1_summarize.get_summary(), step4_2_translate_all.translate_all()), 4),
        ("处理字幕...", lambda: (step5_splitforsub.split_for_sub_main(), step6_generate_final_timeline.align_timestamp_main()), 6),
        ("合并字幕到视频...", step7_merge_sub_to_vid.merge_subtitles_to_video, 7)
    ]
    
    for description, func, step in steps:
        with st.spinner(description):
            func()
        update_progress(progress_bar, step_status, step, total_steps, f"{description.split('...')[0]}完成")
    
    st.success("文本处理完成! 🎉")
    st.balloons()

def audio_processing_section(progress_bar, step_status, total_steps):
    st.header("8-11. 音频处理 🎵")
    with st.expander("展开详情", expanded=True):
        st.info("""
        这个阶段包括以下步骤：

        8. 提取参考音频
        9. 生成音频任务
        10. 使用SoVITS生成音频 (如果出错了请检查命令行输出手动精简 `output/audio/sovits_tasks.xlsx` 中对应行的字幕) (完成后可手动关闭cmd)
        11. 将音频合并到视频中
        """)
        if not os.path.exists("output/output_video_with_audio.mp4"):
            if st.button("开始音频处理", key="audio_processing_button"):
                process_audio(progress_bar, step_status, total_steps)
                st.video("output/output_video_with_audio.mp4") # 展示处理后的视频
                return True
        else:
            update_progress(progress_bar, step_status, total_steps, total_steps, "音频合并到视频完成")
            st.success("音频处理已完成! 🎉")
            st.video("output/output_video_with_audio.mp4")
    return False

def process_audio(progress_bar, step_status, total_steps):
    input_video = (glob.glob("*.mp4") + glob.glob("*.webm"))[0]
    
    steps = [
        ("提取音频...", lambda: step8_extract_refer_audio.step8_main(input_video), 8),
        ("生成音频任务...", step9_generate_audio_task.step9_main, 9),
        ("使用SoVITS生成音频...\n⚠️ 这一步很有可能会因为字幕长度过长而出错，请在运行后根据cmd提示修改对应字幕后重新运行", step10_generate_audio.process_sovits_tasks, 10),
        ("合并音频到视频...", step11_merge_audio_to_vid.merge_all_audio, 11),
    ]
    
    for description, func, step in steps:
        with st.spinner(description):
            func()
        update_progress(progress_bar, step_status, step, total_steps, f"{description.split('...')[0]}完成")
    
    st.success("音频处理完成! 🎉")
    st.balloons()

def main():
    set_page_config()
    st.title("🌉 VideoLingo: 连接世界的每一帧")
    sidebar_info()

    total_steps = 11
    progress_bar, step_status = create_step_progress(total_steps)

    if download_video_section():
        update_progress(progress_bar, step_status, 1, total_steps, "视频下载完成")
        
        if text_processing_section(progress_bar, step_status, total_steps):
            if not os.path.exists("GPT-SoVITS-Inference"):
                st.warning("如需进行配音处理，请将 GPT-SoVITS-Inference 和 uvr5 文件夹放在当前目录下")
            else:
                audio_processing_section(progress_bar, step_status, total_steps)

if __name__ == "__main__":
    main()