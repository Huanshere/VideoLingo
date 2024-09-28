import streamlit as st
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from st_components.i18n import get_localized_string as gls
from core.all_download_methods.download_channel import download_videos_from_channel
from config import YTB_RESOLUTION

def main():
    st.set_page_config(page_title="VideoLingo Bulk Download", page_icon="🎥")

    st.title(gls("bulk_download_title"))

    # Language selection
    language_options = ["Chinese", "English", "Auto"]
    selected_language = st.selectbox(gls("select_language"), options=language_options)

    # YouTube channel URL input
    channel_url = st.text_input(gls("enter_channel_url"), placeholder="https://www.youtube.com/channel/...")

    # Start date input
    start_date = st.date_input(gls("start_date"), datetime.now())

    # Resolution selection
    resolution_options = ["360", "720", "1080", "best"]
    selected_resolution = st.selectbox(gls("select_resolution"), options=resolution_options, index=resolution_options.index(YTB_RESOLUTION))

    if st.button(gls("start_download")):
        if channel_url:
            try:
                with st.spinner(gls("downloading_videos")):
                    save_path = os.path.join('vediolingo-web', 'YouTube_Videos')
                    download_videos_from_channel(channel_url, start_date, resolution=selected_resolution, save_path=save_path)
                st.success(gls("download_complete"))
                st.info(f"{gls('videos_saved_in')} {save_path}")
            except Exception as e:
                st.error(f"{gls('download_error')}: {str(e)}")
        else:
            st.error(gls("enter_valid_url"))

if __name__ == "__main__":
    main()