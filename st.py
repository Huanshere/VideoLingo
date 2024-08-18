import streamlit as st
import os, glob, json, sys
import zipfile, io
from core import step1_ytdlp, step2_whisper_stamped, step3_1_spacy_split, step3_2_splitbymeaning
from core import step4_1_summarize, step4_2_translate_all, step5_splitforsub, step6_generate_final_timeline
from core import step7_merge_sub_to_vid, step8_extract_refer_audio, step9_generate_audio_task
from core import step10_generate_audio, step11_merge_audio_to_vid
from core.onekeycleanup import cleanup
from core.ask_gpt import ask_gpt
from config import step3_2_split_model
# 把当前目录加入系统 os 环境中 以便找到 ffmpeg
current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ['PATH'] += os.pathsep + current_dir

# 检查是否云环境
if sys.platform.startswith('linux'):
    cloud = 1
else:
    cloud = 0

def check_api():
    try:
        response = ask_gpt('this is a test. response {"status": 200} in json format.', model = step3_2_split_model, response_json=True, log_title='test')
        if response['status'] == 200:
            return True
        else:
            return False
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
        st.sidebar.error("😣 api_key 加载有问题 ")
    else:
        st.sidebar.success("🥳 api_key 已加载 开始吧！")

    with st.sidebar.expander("使用前看看 👀", expanded= False):
        # read from docs/QA.json

        faq_data = json.loads(open("docs/QA.json", "r", encoding="utf-8").read())

        for faq in faq_data:
            st.markdown(f"**Q: {faq['question']}**")
            st.markdown(f"A: {faq['answer']}")
            st.markdown("")

    st.sidebar.markdown("🚀 [去 GitHub 打个星](https://github.com/Huanshere/VideoLingo) 🌟")

def create_step_progress():
    progress_bar = st.progress(0)
    step_status = st.empty()
    return progress_bar, step_status

def update_progress(progress_bar, step_status, step, total_steps, description):
    progress = int(step / total_steps * 100)
    progress_bar.progress(progress)
    step_status.markdown(f"**步骤 {step}/{total_steps}**: {description}")

def download_video_section():
    title1 = "1. 上传本地视频 ⏫" if cloud else "1. 从油管链接下载 📥 或 上传本地视频 ⏫"
    st.header(title1)
    with st.expander("展开详情", expanded=True):
        if not glob.glob("*.mp4") + glob.glob("*.webm"):
            info1 = "请上传视频文件" if cloud else "请输入油管链接 或 上传视频文件"
            st.info(info1)

            if not cloud:
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
                
            else:
                return False
        else:
            st.success("视频文件已存在 ✅")
            video_file = (glob.glob("*.mp4") + glob.glob("*.webm"))[0]
            st.video(video_file)
            if st.button("🔄 删除视频重新选择", key="delete_video_button"):
                os.remove(video_file)
                st.rerun()
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
            if st.button("开始处理字幕", key="text_processing_button"):
                process_text(progress_bar, step_status, total_steps)
                st.rerun()
        else:
            update_progress(progress_bar, step_status, 7, total_steps, "字幕合并到视频完成")
            st.success("字幕翻译已完成! 可以在`output`文件夹下查看 srt 文件 ~")
            if cloud:
                st.warning("目前 Linux 下合并中文字幕展示乱码，请下载 srt 文件自行压制处理～")
            st.video("output/output_video_with_subs.mp4") # 展示处理后的视频
            
            # 创建一个内存中的ZIP文件
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                # 添加英文字幕文件
                if os.path.exists("output/english_subtitles.srt"):
                    with open("output/english_subtitles.srt", "rb") as file:
                        zip_file.writestr("english_subtitles.srt", file.read())
                # 添加翻译后的字幕文件
                if os.path.exists("output/translated_subtitles.srt"):
                    with open("output/translated_subtitles.srt", "rb") as file:
                        zip_file.writestr("translated_subtitles.srt", file.read())
            zip_buffer.seek(0)
            
            # 下载按钮
            st.download_button(
                label="📥 下载所有字幕文件",
                data=zip_buffer,
                file_name="subtitles.zip",
                mime="application/zip"
            )
            
            # 一键清理按钮
            if st.button("📦 一键归档到`history`文件夹", key="cleanup_in_text_processing"):
                cleanup()
                st.rerun()
            return True
    return False

def process_text(progress_bar, step_status, total_steps):
    video_file = (glob.glob("*.mp4") + glob.glob("*.webm"))[0]
    
    steps = [
        ("使用Whisper进行转录...", lambda: step2_whisper_stamped.transcript(video_file), 2),
        ("分割长句...", lambda: (step3_1_spacy_split.split_by_spacy(), step3_2_splitbymeaning.split_sentences_by_meaning()), 3),
        ("总结和翻译...", lambda: (step4_1_summarize.get_summary(), step4_2_translate_all.translate_all()), 4),
        ("处理对齐字幕...", lambda: (step5_splitforsub.split_for_sub_main(), step6_generate_final_timeline.align_timestamp_main()), 6),
        ("合并字幕到视频...", step7_merge_sub_to_vid.merge_subtitles_to_video, 7)
    ]
    
    for description, func, step in steps:
        with st.spinner(description):
            func()
        update_progress(progress_bar, step_status, step, total_steps, f"{description.split('...')[0]}完成")
    
    st.success("字幕处理完成! 🎉")
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
            if st.button("开始配音处理", key="audio_processing_button"):
                process_audio(progress_bar, step_status, total_steps)
                st.video("output/output_video_with_audio.mp4") # 展示处理后的视频
                return True
        else:
            update_progress(progress_bar, step_status, total_steps, total_steps, "音频合并到视频完成")
            st.success("配音处理已完成! 可以在`output`文件夹下查看音频文件 ~")
            st.video("output/output_video_with_audio.mp4")
            if st.button("📦 一键归档到`history`文件夹", key="cleanup_in_audio_processing"):
                cleanup()
                st.rerun()
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
    set_page_config()
    st.title("🌉 VideoLingo: 连接世界的每一帧")
    sidebar_info()

    total_steps = 11
    progress_bar, step_status = create_step_progress()

    if download_video_section():
        update_progress(progress_bar, step_status, 1, total_steps, "视频下载完成")
        
        if text_processing_section(progress_bar, step_status, total_steps):
            audio_processing_section(progress_bar, step_status, total_steps)

if __name__ == "__main__":
    main()