import streamlit as st
import os, sys, shutil
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.step1_ytdlp import download_video_ytdlp, find_video_files
from time import sleep

def download_video_section(cloud):
    title1 = "上传视频 " if cloud else "下载或上传视频"
    st.header(title1)
    with st.container(border=True):
        try:
            video_file = find_video_files()
            st.video(video_file)
            if st.button("   删除并重新选择   ", key="delete_video_button"):
                os.remove(video_file)
                if os.path.exists("output"):
                    shutil.rmtree("output")
                sleep(0.5)
                st.rerun()
            return True
        except:
            if not cloud:
                url = st.text_input("输入YouTube链接:")
                if st.button("下载视频", key="download_button", use_container_width=True):
                    if url:
                        with st.spinner("正在下载视频..."):
                            download_video_ytdlp(url)
                        st.rerun()
            from config import ALLOWED_VIDEO_FORMATS
            uploaded_file = st.file_uploader("或上传视频 建议<40min", type=ALLOWED_VIDEO_FORMATS)
            if uploaded_file:
                os.makedirs("output", exist_ok=True)
                # 视频写入output文件夹
                with open(os.path.join("output", uploaded_file.name), "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.rerun()
            else:
                return False