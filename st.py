import streamlit as st
import os, glob, time
from core import step1_ytdlp, step2_whisper_stamped, step3_1_spacy_split, step3_2_splitbymeaning
from core import step4_1_summarize, step4_2_translate_all, step5_splitforsub, step6_generate_final_timeline
from core import step7_merge_sub_to_vid, step8_extract_refer_audio, step9_generate_audio_task
from core import step10_generate_audio, step11_merge_audio_to_vid
from core.onekeycleanup import cleanup
import tqdm

os.environ['STREAMLIT_SERVER_MAX_UPLOAD_SIZE'] = '1028'
# 清除所有代理设置
os.environ.pop('ALL_PROXY', None)
os.environ.pop('all_proxy', None)
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)   

# 在文件开头添加以下代码
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def set_page_config():
    st.set_page_config(page_title="VideoLingo", page_icon="🌉", layout="wide")

def sidebar_info():
    st.sidebar.title("🌟 关于 VideoLingo")
    st.sidebar.info("VideoLingo 是一个全自动视频处理工具。")

def process_video():
    st.header("视频处理")
    
    # 创建两个选项卡
    tab1, tab2 = st.tabs(["上视频", "YouTube链接"])
    
    video_file = None
    
    with tab1:
        uploaded_file = st.file_uploader("上传视频文件", type=["mp4", "webm"])
        if uploaded_file:
            file_details = {"文件名":uploaded_file.name,"文件类型":uploaded_file.type,"文件大小":uploaded_file.size}
            st.write(file_details)
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            speed_text = st.empty()
            
            start_time = time.time()
            total_size = uploaded_file.size
            chunk_size = 1024 * 1024  # 1MB
            
            file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
            with open(file_path, "wb") as f:
                bytes_read = 0
                for chunk in iter(lambda: uploaded_file.read(chunk_size), b''):
                    f.write(chunk)
                    bytes_read += len(chunk)
                    percent_complete = bytes_read / total_size
                    progress_bar.progress(percent_complete)
                    
                    current_time = time.time()
                    elapsed_time = current_time - start_time
                    if elapsed_time > 0:
                        upload_speed = bytes_read / elapsed_time / (1024 * 1024)  # MB/s
                        status_text.text(f"上传进度: {percent_complete:.2%}")
                        speed_text.text(f"上传速度: {upload_speed:.2f} MB/s")
                    
                    time.sleep(0.1)  # 稍微降低更新频率，避免界面卡顿
                
            end_time = time.time()
            total_time = end_time - start_time
            average_speed = total_size / total_time / (1024 * 1024)  # MB/s
            st.success(f"视频上传成功! 平均上传速度: {average_speed:.2f} MB/s")
            video_file = file_path
    
    with tab2:
        url = st.text_input("输入YouTube视频链接:")
        if st.button("下载视频") and url:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            start_time = time.time()
            video_file = step1_ytdlp.download_video_ytdlp(url, save_path=UPLOAD_FOLDER, progress_callback=lambda p: progress_bar.progress(p))
            end_time = time.time()
            
            file_size = os.path.getsize(video_file)
            download_speed = file_size / (end_time - start_time) / (1024 * 1024)  # MB/s
            st.success(f"视频下载成功! 平均下载速度: {download_speed:.2f} MB/s")

    # 添加视频预览功能
    if video_file:
        st.subheader("视频预览")
        video_preview = st.empty()
        with video_preview.container():
            st.video(video_file, start_time=0)
        
        # 添加控制选项
        col1, col2 = st.columns(2)
        with col1:
            start_time = st.number_input("开始时间（秒）", min_value=0, value=0, step=1)
        with col2:
            duration = st.number_input("持续时间（秒）", min_value=1, value=10, step=1)
        
        if st.button("更新预览"):
            with video_preview.container():
                st.video(video_file, start_time=int(start_time))
            st.info(f"预览视���从 {start_time} 秒开始，持续 {duration} 秒")

    # 处理视频
    if video_file:
        use_gpu = st.checkbox("使用GPU加速（如果可用）", value=True)

        if st.button("开始处理"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            initial_steps = [
                ("转录音频", lambda: step2_whisper_stamped.transcript(video_file)),
                ("分割句子 (spaCy)", step3_1_spacy_split.split_by_spacy),
                ("分割句子 (意义)", step3_2_splitbymeaning.split_sentences_by_meaning),
                ("生成摘要", step4_1_summarize.get_summary),
                ("翻译内容", step4_2_translate_all.translate_all),
                ("分割字幕", step5_splitforsub.split_for_sub_main),
                ("对齐时间轴", step6_generate_final_timeline.align_timestamp_main),
                ("合并字幕到视频", lambda: step7_merge_sub_to_vid.merge_subtitles_to_video(video_file, use_gpu)),
            ]
            
            for i, (step_name, step_func) in enumerate(initial_steps):
                status_text.text(f"正在处理: {step_name}")
                st.text(f"开始 {step_name}")
                step_start_time = time.time()
                try:
                    result = step_func()
                    if result is False:
                        st.error(f"{step_name} 失败。请检查日志以获取更多信息。")
                        break
                except Exception as e:
                    st.error(f"{step_name} 发生错误: {str(e)}")
                    st.text(f"误详情: {type(e).__name__}: {str(e)}")
                    break
                step_end_time = time.time()
                progress_bar.progress((i + 1) / len(initial_steps))
                status_text.text(f"完成: {step_name} (耗时: {step_end_time - step_start_time:.2f}秒)")
                st.text(f"完成 {step_name}")
                
                # 在每个步骤后检查文件
                st.text("检查生成的文件...")
                if step_name == "分割字幕":
                    if os.path.exists("output/split_subtitles.json"):
                        st.text("分割后的字幕RRRR")
                    else:
                        st.error("分割后的字幕文件不存在")
                        break
                elif step_name == "对齐时间轴":
                    if os.path.exists("output/english_subtitles.srt"):
                        st.text("英文字幕文件存在")
                    else:
                        st.error("英文字幕文件不存在")
                    if os.path.exists("output/translated_subtitles.srt"):
                        st.text("翻译字幕文件存在")
                    else:
                        st.error("翻译字幕文件不存在")
                    
                    if not os.path.exists("output/translated_subtitles.srt") or not os.path.exists("output/english_subtitles.srt"):
                        st.error("字幕文件未生成。请检查之前的步骤。")
                        break
                
                time.sleep(0.5)
            
            if os.path.exists("output/output_with_subtitles.mp4"):
                st.success("字幕已成功合并到视频中!")
                st.video("output/output_with_subtitles.mp4")
                
                # 添加用户选择
                if st.button("继续进行音频合成和合并"):
                    audio_steps = [
                        ("提取参考音频", lambda: step8_extract_refer_audio.step8_main(video_file, use_gpu)),
                        ("生成音频任务", step9_generate_audio_task.step9_main),
                        ("生成音频", step10_generate_audio.process_sovits_tasks),
                        ("合并音频到视频", step11_merge_audio_to_vid.merge_main)
                    ]
                    
                    for i, (step_name, step_func) in enumerate(audio_steps):
                        status_text.text(f"正在处理: {step_name}")
                        st.text(f"开始 {step_name}")
                        step_start_time = time.time()
                        try:
                            result = step_func()
                            if result is False:
                                st.error(f"{step_name} 失败。请检查日志以获取更多信息。")
                                break
                        except Exception as e:
                            st.error(f"{step_name} 发生错误: {str(e)}")
                            break
                        step_end_time = time.time()
                        progress_bar.progress((i + 1) / len(audio_steps))
                        status_text.text(f"完成: {step_name} (耗时: {step_end_time - step_start_time:.2f}秒)")
                        st.text(f"完成 {step_name}")
                        
                        time.sleep(0.5)
                    
                    if os.path.exists("output/output_video_with_audio.mp4"):
                        st.success("音频合成和合并完成!")
                        st.video("output/output_video_with_audio.mp4")
                    else:
                        st.error("音频合成和合并未完成。最终视频文件未生成。")
            else:
                st.error("处理未完成。带字幕的视频文件未生成。")

def main():
    set_page_config()
    sidebar_info()
    process_video()

    if st.button("清理文件"):
        cleanup()
        st.success("文件已清理")

if __name__ == "__main__":
    main()
