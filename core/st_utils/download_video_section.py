import os
import re
import shutil
from time import sleep

import streamlit as st
from core._1_ytdlp import download_video_ytdlp, find_media_file, write_input_manifest
from core.utils import *
from translations.translations import translate as t

OUTPUT_DIR = "output"


def _css_text(value):
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def _inject_file_uploader_i18n():
    # Streamlit does not expose official i18n for file_uploader internals.
    # Streamlit 1.49 DOM:
    #   div[data-testid="stFileUploaderDropzoneInstructions"]
    #     > span    (cloud icon, must keep)
    #     > div     (column flex)
    #         > span  (1st: "Drag and drop ... here")
    #         > span  (2nd: "Limit ... · MP4, MOV ...")
    # So we target ONLY the two direct child spans of the inner div, leaving
    # the icon and other elements untouched.
    drag_text = _css_text(t("Drag and drop file here"))
    limit_text = _css_text(t("Limit 4GB per file · MP4, MOV, AVI, MKV, FLV, WMV, WEBM, WAV, MP3, FLAC, M4A"))
    browse_text = _css_text(t("Browse files"))
    st.markdown(
        f"""
        <style>
        /* Title line */
        .st-key-main_media_upload div[data-testid="stFileUploaderDropzoneInstructions"] > div > span:nth-of-type(1) {{
            font-size: 0 !important;
            line-height: 1.4;
        }}
        .st-key-main_media_upload div[data-testid="stFileUploaderDropzoneInstructions"] > div > span:nth-of-type(1)::before {{
            content: "{drag_text}";
            font-size: 1rem;
        }}
        /* Sub line (limit + accepted formats) */
        .st-key-main_media_upload div[data-testid="stFileUploaderDropzoneInstructions"] > div > span:nth-of-type(2) {{
            font-size: 0 !important;
            line-height: 1.4;
        }}
        .st-key-main_media_upload div[data-testid="stFileUploaderDropzoneInstructions"] > div > span:nth-of-type(2)::before {{
            content: "{limit_text}";
            font-size: 0.8rem;
        }}
        /* Browse files button */
        .st-key-main_media_upload div[data-testid="stFileUploader"] button[kind="secondary"] {{
            font-size: 0 !important;
        }}
        .st-key-main_media_upload div[data-testid="stFileUploader"] button[kind="secondary"]::before {{
            content: "{browse_text}";
            font-size: 0.875rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def download_video_section():
    st.header(t("a. Download or Upload Video"))
    with st.container(border=True):
        try:
            media_file, media_type = find_media_file()
            if media_type == "video":
                st.video(media_file)
            else:
                st.audio(media_file)
            if st.button(t("Delete and Reselect"), key="delete_video_button"):
                os.remove(media_file)
                if os.path.exists(OUTPUT_DIR):
                    shutil.rmtree(OUTPUT_DIR)
                st.session_state.pop("_processed_upload_id", None)
                sleep(1)
                st.rerun()
            return True
        except ValueError as e:
            if "No media file found" not in str(e):
                st.error(t("Media file detection failed: {error}").replace("{error}", str(e)))
                if st.button(t("Clear output and reselect"), key="clear_output_button"):
                    if os.path.exists(OUTPUT_DIR):
                        shutil.rmtree(OUTPUT_DIR)
                    st.session_state.pop("_processed_upload_id", None)
                    st.rerun()
                return False
        except Exception:
            pass

        col1, col2 = st.columns([3, 1])
        with col1:
            url = st.text_input(t("Enter YouTube link:"))
        with col2:
            res_dict = {
                "360p": "360",
                "1080p": "1080",
                t("Best"): "best"
            }
            target_res = load_key("ytb_resolution")
            res_options = list(res_dict.keys())
            default_idx = list(res_dict.values()).index(target_res) if target_res in res_dict.values() else 0
            res_display = st.selectbox(t("Resolution"), options=res_options, index=default_idx)
            res = res_dict[res_display]
        if st.button(t("Download Video"), key="download_button", width="stretch"):
            if url:
                with st.spinner(t("Downloading video...")):
                    download_video_ytdlp(url, resolution=res)
                st.rerun()

        _inject_file_uploader_i18n()
        uploaded_file = st.file_uploader(
            t("Upload local media file"),
            type=load_key("allowed_video_formats") + load_key("allowed_audio_formats"),
            key="main_media_upload",
        )
        if uploaded_file:
            upload_id = f"{uploaded_file.name}:{uploaded_file.size}"
            if st.session_state.get("_processed_upload_id") == upload_id:
                try:
                    find_media_file()
                    st.warning(t("Upload was already processed. Delete and reselect to upload again."))
                    return False
                except Exception:
                    st.session_state.pop("_processed_upload_id", None)

            if os.path.exists(OUTPUT_DIR):
                shutil.rmtree(OUTPUT_DIR)
            os.makedirs(OUTPUT_DIR, exist_ok=True)

            raw_name = uploaded_file.name.replace(' ', '_')
            name, ext = os.path.splitext(raw_name)
            clean_name = re.sub(r'[^\w\-_\.]', '', name) + ext.lower()
                
            with open(os.path.join(OUTPUT_DIR, clean_name), "wb") as f:
                f.write(uploaded_file.getbuffer())

            media_path = os.path.join(OUTPUT_DIR, clean_name)
            media_ext = ext.lower().lstrip(".")
            media_type = "video" if media_ext in load_key("allowed_video_formats") else "audio"
            write_input_manifest(media_path, media_type)

            st.session_state["_processed_upload_id"] = upload_id
            st.rerun()
        else:
            return False
