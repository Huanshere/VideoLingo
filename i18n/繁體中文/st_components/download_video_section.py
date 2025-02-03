import streamlit as st
import os, sys, shutil
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config_utils import load_key
from core.step1_ytdlp import download_video_ytdlp, find_video_files
from time import sleep
import re
import subprocess

def download_video_section():
    st.header("下載或上傳影片")
    with st.container(border=True):
        try:
            video_file = find_video_files()
            st.video(video_file)
            if st.button("刪除並重新選擇", key="delete_video_button"):
                os.remove(video_file)
                if os.path.exists("output"):
                    shutil.rmtree("output")
                sleep(1)
                st.rerun()
            return True
        except:
            col1, col2 = st.columns([3, 1])
            with col1:
                url = st.text_input("輸入YouTube連結:")
            with col2:
                res_dict = {
                    "360p": "360",
                    "1080p": "1080",
                    "最佳": "best"
                }
                target_res = load_key("ytb_resolution")
                res_options = list(res_dict.keys())
                default_idx = list(res_dict.values()).index(target_res) if target_res in res_dict.values() else 0
                res_display = st.selectbox("分辨率", options=res_options, index=default_idx)
                res = res_dict[res_display]
            if st.button("下載影片", key="download_button", use_container_width=True):
                if url:
                    with st.spinner("正在下載影片..."):
                        download_video_ytdlp(url, resolution=res)
                    st.rerun()

            uploaded_file = st.file_uploader("或上傳影片", type=load_key("allowed_video_formats") + load_key("allowed_audio_formats"))
            if uploaded_file:
                if os.path.exists("output"):
                    shutil.rmtree("output")
                os.makedirs("output", exist_ok=True)
                
                raw_name = uploaded_file.name.replace(' ', '_')
                name, ext = os.path.splitext(raw_name)
                clean_name = re.sub(r'[^\w\-_\.]', '', name) + ext.lower()
                
                with open(os.path.join("output", clean_name), "wb") as f:
                    f.write(uploaded_file.getbuffer())

                if clean_name.split('.')[-1] in load_key("allowed_audio_formats"):
                    convert_audio_to_video(os.path.join("output", clean_name))
                st.rerun()
            else:
                return False

def convert_audio_to_video(audio_file: str) -> str:
    output_video = 'output/black_screen.mp4'
    if not os.path.exists(output_video):
        print(f"🎵➡️🎬 正在使用FFmpeg將音訊轉換為影片......")
        ffmpeg_cmd = ['ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=black:s=640x360', '-i', audio_file, '-shortest', '-c:v', 'libx264', '-c:a', 'aac', '-pix_fmt', 'yuv420p', output_video]
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True, encoding='utf-8')
        print(f"🎵➡️🎬 已將 <{audio_file}> 轉換為 <{output_video}> with FFmpeg\n")
        os.remove(audio_file)
    return output_video
