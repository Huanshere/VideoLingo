import streamlit as st
import os, sys, shutil
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config_utils import load_key
from core.step1_ytdlp import download_video_ytdlp, find_video_files
from i18n.st_i18n import get_localized_string
from time import sleep
import re

def download_video_section():
    title1 = get_localized_string("download_or_upload_video")
    st.header(title1)
    with st.container(border=True):
        try:
            video_file = find_video_files()
            st.video(video_file)
            if st.button(get_localized_string("delete_and_reselect"), key="delete_video_button"):
                os.remove(video_file)
                if os.path.exists("output"):
                    shutil.rmtree("output")
                sleep(1)
                st.rerun()
            return True
        except:
            col1, col2 = st.columns([3, 1])
            with col1:
                url = st.text_input(get_localized_string("enter_youtube_link"))
            with col2:
                resolution_dict = {
                    "360p": "360",
                    "1080p": "1080",
                    "Best": "best"
                }
                YTB_RESOLUTION = load_key("ytb_resolution")
                resolution_options = list(resolution_dict.keys())
                default_index = list(resolution_dict.values()).index(YTB_RESOLUTION) if YTB_RESOLUTION in resolution_dict.values() else 0
                resolution_display = st.selectbox("Resolution", options=resolution_options, index=default_index)
                resolution = resolution_dict[resolution_display]
            if st.button(get_localized_string("download_video"), key="download_button", use_container_width=True):
                if url:
                    with st.spinner(get_localized_string("downloading_video")):
                        download_video_ytdlp(url, resolution=resolution)
                    st.rerun()

            uploaded_file = st.file_uploader(get_localized_string("or_upload_video"), type=load_key("allowed_video_formats"))
            if uploaded_file:
                #delte file in output
                if os.path.exists("output"):
                    shutil.rmtree("output")
                os.makedirs("output", exist_ok=True)
                # Normalize filename
                normalized_name = re.sub(r'[^\w\-_\.]', '', uploaded_file.name.replace(' ', '_'))
                # Save uploaded video with normalized name
                with open(os.path.join("output", normalized_name), "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.rerun()
            else:
                return False