import streamlit as st
import os, glob, time
from core import step1_ytdlp, step2_whisper_stamped, step3_1_spacy_split, step3_2_splitbymeaning
from core import step4_1_summarize, step4_2_translate_all, step5_splitforsub, step6_generate_final_timeline
from core import step7_merge_sub_to_vid, step8_extract_refer_audio, step9_generate_audio_task
from core import step10_generate_audio, step11_merge_audio_to_vid
from core.onekeycleanup import cleanup
import tqdm
import logging
import traceback

# 设置页面配置
st.set_page_config(page_title="VideoLingo", page_icon="🌉", layout="wide")

os.environ['STREAMLIT_SERVER_MAX_UPLOAD_SIZE'] = '1028'

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clear_proxy_settings():
    logger.info("开始清除代理设置")
    proxy_vars = ['http_proxy', 'https_proxy', 'ftp_proxy', 'no_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'FTP_PROXY', 'NO_PROXY', 'SOCKS_PROXY', 'socks_proxy']
    for var in proxy_vars:
        if var in os.environ:
            logger.debug(f"删除环境变量: {var}")
            del os.environ[var]
    
    # 设置 no_proxy 为 *，这将禁用所有代理
    logger.debug("设置 no_proxy 和 NO_PROXY 为 '*'")
    os.environ['no_proxy'] = '*'
    os.environ['NO_PROXY'] = '*'
    logger.info("代理设置清除完成")

def sidebar_info():
    st.sidebar.title("🌟 关于 VideoLingo")
    st.sidebar.info("VideoLingo 是一个全自动视频处理工具。")

def process_video():
    st.header("视频处理")
    
    tab1, tab2 = st.tabs(["上传视频", "YouTube链接"])
    
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
            
            with open(os.path.join("./", uploaded_file.name), "wb") as f:
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
            video_file = uploaded_file.name
            
            # 显示视频预览
            st.subheader("视频预览")
            st.video(video_file)
            
            # 显示处理按钮
            if st.button("开始处理视频"):
                process_downloaded_video(video_file)
    
    with tab2:
        url = st.text_input("输入YouTube视频链接:")
        download_button = st.button("下载视频")
        
        if download_button and url:
            progress_bar = st.progress(0)
            status_text = st.empty()
            speed_text = st.empty()
            
            try:
                video_file = step1_ytdlp.download_video_ytdlp(url, save_path='./', progress_callback=lambda p: update_progress(p, progress_bar, status_text, speed_text))
                
                st.success(f"视频下载成功!")
                
                # 显示视频预览
                st.subheader("视频预览")
                st.video(video_file)
                
            except Exception as e:
                st.error(f"下载过程中发生错误: {str(e)}")
                return

        # 将处理按钮移到这里，确它在下载完成后才显示
        if video_file and st.button("开始处理下载的视频"):
            process_downloaded_video(video_file)

def process_downloaded_video(video_file):
    logger.info("开始处理视频")
    clear_proxy_settings()
    logger.debug("代理设置已清除")
    
    # 创建 Streamlit 元素用于显示进度和状态
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    st.info("开始处理视频...")
    
    # 添加 GPU 选项
    use_gpu = st.checkbox("使用GPU加速（如果可用）", value=True)
    
    try:
        initial_steps = [
            ("转录音频", lambda: step2_whisper_stamped.transcript(video_file)),
            ("分割句子 (spaCy)", step3_1_spacy_split.split_by_spacy),
            ("分割句子 (意义)", lambda: step3_2_splitbymeaning.split_sentences_by_meaning()),
            ("总结", step4_1_summarize.get_summary),  # 更新这一行
            ("翻译", step4_2_translate_all.translate_all),
            ("分割字幕", step5_splitforsub.split_for_sub_main),
            ("生成最终时间轴", step6_generate_final_timeline.align_timestamp_main),
            ("合并字幕到视频", lambda: step7_merge_sub_to_vid.merge_subtitles_to_video(video_file, use_gpu)),
        ]
        
        for i, (step_name, step_func) in enumerate(initial_steps):
            logger.info(f"开始执行步骤: {step_name}")
            status_text.text(f"正在处理: {step_name}")
            st.text(f"开始 {step_name}")
            try:
                result = step_func()
                if result is False:
                    logger.error(f"{step_name} 失败")
                    st.error(f"{step_name} 失败。请检查日志以获取更多信息。")
                    break
                logger.info(f"完成步骤: {step_name}")
                st.success(f"完成 {step_name}")
            except Exception as e:
                logger.exception(f"{step_name} 发生错误")
                st.error(f"{step_name} 发生错误: {str(e)}")
                st.text(f"错误详情: {type(e).__name__}: {str(e)}")
                st.text(f"错误堆栈: {traceback.format_exc()}")
                break
            progress_bar.progress((i + 1) / len(initial_steps))
        
        if os.path.exists("output/output_with_subtitles.mp4"):
            st.success("处理完成！")
            st.video("output/output_with_subtitles.mp4")
        else:
            st.warning("处理可能未完全成功。请检查输出文件。")
    
    except Exception as e:
        logger.exception("处理视频时发生未捕获的异常")
        st.error(f"处理过程中发生错误: {str(e)}")
        st.text(f"错误堆栈: {traceback.format_exc()}")

    finally:
        # 清理进度条和状态文本
        progress_bar.empty()
        status_text.empty()

@st.cache_data
def load_video_file(file_path):
    return open(file_path, "rb").read()

def update_progress(progress, progress_bar, status_text, speed_text, start_time):
    progress_bar.progress(progress)
    current_time = time.time()
    elapsed_time = current_time - start_time
    if elapsed_time > 0:
        download_speed = progress / elapsed_time / (1024 * 1024)  # MB/s
        status_text.text(f"下载进度: {progress:.2%}")
        speed_text.text(f"下载速度: {download_speed:.2f} MB/s")

def main():
    sidebar_info()
    process_video()

    if st.button("清理文件"):
        cleanup()
        st.success("文件已清理")

if __name__ == "__main__":
    main()
