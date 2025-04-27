import os
import streamlit as st
import io, zipfile
from core.st_utils.download_video_section import download_video_section
from core.st_utils.sidebar_setting import page_setting
from translations.translations import translate as t

def download_subtitle_zip_button(text: str):
    zip_buffer = io.BytesIO()
    output_dir = "output"
    
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for file_name in os.listdir(output_dir):
            if file_name.endswith(".srt"):
                file_path = os.path.join(output_dir, file_name)
                with open(file_path, "rb") as file:
                    zip_file.writestr(file_name, file.read())
    
    zip_buffer.seek(0)
    
    st.download_button(
        label=text,
        data=zip_buffer,
        file_name="subtitles.zip",
        mime="application/zip"
    )

# st.markdown
give_star_button = """
<style>
    .github-button {
        display: block;
        width: 100%;
        padding: 0.5em 1em;
        color: #144070;
        background-color: #d0e0f2;
        border-radius: 6px;
        text-decoration: none;
        font-weight: bold;
        text-align: center;
        transition: background-color 0.3s ease, color 0.3s ease;
        box-sizing: border-box;
    }
    .github-button:hover {
        background-color: #ffffff;
        color: #144070;
    }
</style>
<a href="https://github.com/Huanshere/VideoLingo" target="_blank" style="text-decoration: none;">
    <div class="github-button">
        Star on GitHub 🌟
    </div>
</a>
"""

button_style = """
<style>
div.stButton > button:first-child {
    display: block;
    padding: 0.5em 1em;
    color: #144070;
    background-color: transparent;
    text-decoration: none;
    font-weight: bold;
    text-align: center;
    transition: all 0.3s ease;
    box-sizing: border-box;
    border: 2px solid #D0DFF2;
    font-size: 1.2em;
}
div.stButton > button:hover {
    background-color: transparent;
    color: #144070;
    border-color: #144070;
}
div.stButton > button:active, div.stButton > button:focus {
    background-color: transparent !important;
    color: #144070 !important;
    border-color: #144070 !important;
    box-shadow: none !important;
}
div.stButton > button:active:hover, div.stButton > button:focus:hover {
    background-color: transparent !important;
    color: #144070 !important;
    border-color: #144070 !important;
    box-shadow: none !important;
}
div.stDownloadButton > button:first-child {
    display: block;
    padding: 0.5em 1em;
    color: #144070;
    background-color: transparent;
    text-decoration: none;
    font-weight: bold;
    text-align: center;
    transition: all 0.3s ease;
    box-sizing: border-box;
    border: 2px solid #D0DFF2;
    font-size: 1.2em;
}
div.stDownloadButton > button:hover {
    background-color: transparent;
    color: #144070;
    border-color: #144070;
}
div.stDownloadButton > button:active, div.stDownloadButton > button:focus {
    background-color: transparent !important;
    color: #144070 !important;
    border-color: #144070 !important;
    box-shadow: none !important;
}
div.stDownloadButton > button:active:hover, div.stDownloadButton > button:focus:hover {
    background-color: transparent !important;
    color: #144070 !important;
    border-color: #144070 !important;
    box-shadow: none !important;
}
</style>
"""