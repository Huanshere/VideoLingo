import streamlit as st
import os, glob
from core import step1_ytdlp, step2_whisper_stamped, step3_1_spacy_split, step3_2_splitbymeaning
from core import step4_1_summarize, step4_2_translate_all, step5_splitforsub, step6_generate_final_timeline
from core import step7_merge_sub_to_vid, step8_extract_refer_audio, step9_generate_audio_task
from core import step10_generate_audio, step11_merge_audio_to_vid
from core.onekeycleanup import cleanup
from core.ask_gpt import ask_gpt
from config import step3_2_split_model

def check_api():
    try:
        ask_gpt('this is a test. response {"status": 200} in json format.', model = step3_2_split_model, response_json=True, log_title='test')
        return True
    except:
        return False

def set_page_config():
    st.set_page_config(
        page_title="VideoLingo: 连接世界的每一帧",
        page_icon="🌉",
        layout="wide",
        initial_sidebar_state="expanded",
    )

def sidebar_info():
    api_status = check_api()
    st.sidebar.title("🌟 关于 VideoLingo")
    st.sidebar.info("VideoLingo 是一个全自动烤肉机，可以下载视频、转录音频、翻译内容、生成专业级字幕，甚至还可以进行个性化配音。")
    
    if not api_status:
        st.sidebar.warning("⚠️ 请检查 `config.py` 的 api_key 是否正确填写")
    else:
        st.sidebar.success("✅ api_key 已加载，开始视频本地化之旅吧！")

    with st.sidebar.expander("常见问题", expanded= False):
        faq_data = [
            {
                "question": "为什么处理得这么慢？",
                "answer": "视频翻译难的不在翻译，而在字幕分割和对齐，此外本项目还进行了专有名词提取、多步翻译。若追求速度推荐 **沉浸式翻译** Chrome插件"
            },
            {
                "question": "支持什么语言？",
                "answer": "理论上输入输出支持所有语言，注意修改 `config.py` 中的设定。"
            },
            {
                "question": "我可以自行编辑处理好的 srt 文件吗？",
                "answer": "是的，所有的输出文件都在`output`目录下，输出的视频仅为低分辨率的 demo，更推荐自行校对和压制"
            },
            {
                "question": "消耗 api 金额大吗？",
                "answer": "在推荐配置下，5min 视频只需要 1 元。如果降低质量要求，可以在`config.py`中调整为全使用`deepseek-coder`，近乎免费"
            }
        ]

        for faq in faq_data:
            st.markdown(f"**Q: {faq['question']}**")
            st.markdown(f"A: {faq['answer']}")
            st.markdown("")

    st.sidebar.markdown("🚀 [看看 GitHub 仓库](https://github.com/Huanshere/VideoLingo) 🌟")

def create_step_progress():
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
            
            uploaded_file = st.file_uploader("或者上传视频文件", type=["mp4", "webm"])
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
    st.header("2-7. 字幕翻译生成 📝")
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
    st.header("8-11. SoVits 配音 🎵")
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
        ("使用SoVITS生成音频...\n⚠️ 如果这一步因字幕出错，请根据cmd提示修改对应字幕后重新运行", step10_generate_audio.process_sovits_tasks, 10),
        ("合并音频到视频...", step11_merge_audio_to_vid.merge_main, 11),
    ]
    
    for description, func, step in steps:
        with st.spinner(description):
            func()
        update_progress(progress_bar, step_status, step, total_steps, f"{description.split('...')[0]}完成")
    
    st.success("音频处理完成! 🎉")
    st.balloons()

def main():
    check_api()
    set_page_config()
    st.title("🌉 VideoLingo: 连接世界的每一帧")
    sidebar_info()

    total_steps = 11
    progress_bar, step_status = create_step_progress()

    if download_video_section():
        update_progress(progress_bar, step_status, 1, total_steps, "视频下载完成")
        
        if text_processing_section(progress_bar, step_status, total_steps):
            if audio_processing_section(progress_bar, step_status, total_steps):
                if st.button("📦 一键归档历史记录", key="cleanup_button"):
                    cleanup()

if __name__ == "__main__":
    main()