import os
import re
import shutil
import subprocess
from time import sleep

import streamlit as st
from core._1_ytdlp import download_video_ytdlp, find_video_files
from core.utils import *
from translations.translations import translate as t

OUTPUT_DIR = "output"

def download_video_section():
    st.header(t("a. Download or Upload Video"))
    with st.container(border=True):
        try:
            video_file = find_video_files()
            st.video(video_file)
            if st.button(t("Delete and Reselect"), key="delete_video_button"):
                os.remove(video_file)
                if os.path.exists(OUTPUT_DIR):
                    shutil.rmtree(OUTPUT_DIR)
                sleep(1)
                st.rerun()
            return True
        except:
            col1, col2 = st.columns([3, 1])
            with col1:
                url = st.text_input(t("Enter YouTube link:"))
            with col2:
                res_dict = {
                    "360p": "360",
                    "1080p": "1080",
                    "Best": "best"
                }
                target_res = load_key("ytb_resolution")
                res_options = list(res_dict.keys())
                default_idx = list(res_dict.values()).index(target_res) if target_res in res_dict.values() else 0
                res_display = st.selectbox(t("Resolution"), options=res_options, index=default_idx)
                res = res_dict[res_display]
            if st.button(t("Download Video"), key="download_button", use_container_width=True):
                if url:
                    with st.spinner("Downloading video..."):
                        download_video_ytdlp(url, resolution=res)
                    st.rerun()

            uploaded_file = st.file_uploader(t("Or upload video"), type=load_key("allowed_video_formats") + load_key("allowed_audio_formats"))
            if uploaded_file:
                if os.path.exists(OUTPUT_DIR):
                    shutil.rmtree(OUTPUT_DIR)
                os.makedirs(OUTPUT_DIR, exist_ok=True)
                
                raw_name = uploaded_file.name.replace(' ', '_')
                name, ext = os.path.splitext(raw_name)
                clean_name = re.sub(r'[^\w\-_\.]', '', name) + ext.lower()
                    
                with open(os.path.join(OUTPUT_DIR, clean_name), "wb") as f:
                    f.write(uploaded_file.getbuffer())

                if ext.lower() in load_key("allowed_audio_formats"):
                    convert_audio_to_video(os.path.join(OUTPUT_DIR, clean_name))
                st.rerun()
            else:
                return False

def convert_audio_to_video(audio_file: str) -> str:
    output_video = os.path.join(OUTPUT_DIR, 'black_screen.mp4')
    if not os.path.exists(output_video):
        print(f"🎵➡️🎬 Converting audio to video with FFmpeg ......")
        ffmpeg_cmd = ['ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=black:s=640x360', '-i', audio_file, '-shortest', '-c:v', 'libx264', '-c:a', 'aac', '-pix_fmt', 'yuv420p', output_video]
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True, encoding='utf-8')
        print(f"🎵➡️🎬 Converted <{audio_file}> to <{output_video}> with FFmpeg\n")
        # delete audio file
        os.remove(audio_file)
    return output_video
