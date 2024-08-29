import streamlit as st
import os, glob, sys, shutil
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from st_components.imports_and_utils import step1_ytdlp

def download_video_section(cloud):
    title1 = "上传视频 " if cloud else "下载或上传视频"
    st.header(title1)
    with st.container(border=True):
        if not glob.glob("*.mp4") + glob.glob("*.webm"):
            if not cloud:
                url = st.text_input("输入YouTube链接:")
                if st.button("下载视频", key="download_button", use_container_width=True):
                    if url:
                        with st.spinner("正在下载视频..."):
                            step1_ytdlp.download_video_ytdlp(url, save_path='./')
                        st.rerun()
            
            uploaded_file = st.file_uploader("或上传视频 <30min", type=["mp4", "webm"])
            if uploaded_file:
                with open(os.path.join("./", uploaded_file.name), "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.video(uploaded_file)
                st.rerun()
            else:
                return False
        else:
            video_file = (glob.glob("*.mp4") + glob.glob("*.webm"))[0]
            st.video(video_file)
            if st.button("   删除并重新选择   ", key="delete_video_button"):
                os.remove(video_file)
                if os.path.exists("output"):
                    shutil.rmtree("output")
                st.rerun()
            return True