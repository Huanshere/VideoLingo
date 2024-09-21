import re
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from st_components.imports_and_utils import ask_gpt
import config
import streamlit as st
from st_components.i18n import get_system_language, get_localized_string
import time

def update_config(key, value):
    with open('config.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    pattern = rf"^{re.escape(key)}\s*=.*$"
    replacement = f"{key} = {repr(value)}"
    new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    with open('config.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
def init_display_language():
    if config.DISPLAY_LANGUAGE == "auto":
        display_language = get_system_language()
        update_config("DISPLAY_LANGUAGE", display_language)
        config.DISPLAY_LANGUAGE = display_language
        time.sleep(0.2)
        st.rerun()

def page_setting():
    init_display_language()
    changes = {}  # save changes

    st.header(get_localized_string("llm_config"))
    
    api_key = st.text_input("API_KEY", value=config.API_KEY, help=get_localized_string("api_key_help"))
    if api_key != config.API_KEY:
        changes["API_KEY"] = api_key

    selected_base_url = st.text_input("BASE_URL", value=config.BASE_URL, help=get_localized_string("base_url_help"))
    if selected_base_url != config.BASE_URL:
        changes["BASE_URL"] = selected_base_url

    model = st.text_input("MODEL", value=config.MODEL[0] if config.MODEL else "")
    if model and model != config.MODEL[0]:
        changes["MODEL"] = [model]
    
    st.header(get_localized_string("subtitle_settings"))
    whisper_method_options = ["whisperx", "whisperxapi"]
    selected_whisper_method = st.selectbox(get_localized_string("whisper_method"), options=whisper_method_options, index=whisper_method_options.index(config.WHISPER_METHOD) if config.WHISPER_METHOD in whisper_method_options else 0)
    if selected_whisper_method != config.WHISPER_METHOD:
        changes["WHISPER_METHOD"] = selected_whisper_method
    if selected_whisper_method == "whisperxapi":    
        replicate_api_token = st.text_input(get_localized_string("replicate_api_token"), value=config.REPLICATE_API_TOKEN, help=get_localized_string("replicate_api_token_help"))
        if replicate_api_token != config.REPLICATE_API_TOKEN:
            changes["REPLICATE_API_TOKEN"] = replicate_api_token
        
    lang_cols = st.columns(2)
    with lang_cols[0]:
        whisper_language_options = ["auto", "en"]
        selected_whisper_language = st.selectbox(get_localized_string("whisper_recognition_language"), options=whisper_language_options, index=whisper_language_options.index(config.WHISPER_LANGUAGE) if config.WHISPER_LANGUAGE in whisper_language_options else 0, help=get_localized_string("whisper_recognition_language_help"))
        if selected_whisper_language != config.WHISPER_LANGUAGE:
            changes["WHISPER_LANGUAGE"] = selected_whisper_language
    with lang_cols[1]:
        target_language = st.text_input(get_localized_string("translation_target_language"), value=config.TARGET_LANGUAGE, help=get_localized_string("translation_target_language_help"))
        if target_language != config.TARGET_LANGUAGE:
            changes["TARGET_LANGUAGE"] = target_language

    st.write(get_localized_string("subtitle_line_length_settings"))
    max_length_cols = st.columns(2)
    with max_length_cols[0]:
        max_src_length = st.number_input(get_localized_string("max_characters_per_line"), value=config.MAX_SUB_LENGTH, help=get_localized_string("max_characters_per_line_help"))
        if max_src_length != config.MAX_SUB_LENGTH:
            changes["MAX_SUB_LENGTH"] = int(max_src_length)
    with max_length_cols[1]:
        target_sub_multiplier = st.number_input(get_localized_string("translation_length_multiplier"), value=config.TARGET_SUB_MULTIPLIER, help=get_localized_string("translation_length_multiplier_help"))
        if target_sub_multiplier != config.TARGET_SUB_MULTIPLIER:
            changes["TARGET_SUB_MULTIPLIER"] = int(target_sub_multiplier)

    resolution_options = {
        "1080p": "1920x1080",
        "360p": "640x360",
        "No video": "0x0"
    }
    selected_resolution = st.selectbox(get_localized_string("video_resolution"), options=list(resolution_options.keys()), index=list(resolution_options.values()).index(config.RESOLUTION))
    resolution = resolution_options[selected_resolution]
    if resolution != config.RESOLUTION:
        changes["RESOLUTION"] = resolution
    
    display_language_options = ["zh_CN", "en_US", "auto"]
    selected_display_language = st.selectbox(get_localized_string("display_language"), options=display_language_options, index=display_language_options.index(config.DISPLAY_LANGUAGE) if config.DISPLAY_LANGUAGE in display_language_options else 0)
    if selected_display_language != config.DISPLAY_LANGUAGE:
        changes["DISPLAY_LANGUAGE"] = selected_display_language

    if changes:
        st.toast(get_localized_string("remember_save_settings"), icon="🔔")
    
    st.markdown("")
    cols_save = st.columns(2)
    with cols_save[0]:
        if st.button(get_localized_string("save"), use_container_width = True):
            for key, value in changes.items():
                update_config(key, value)
            st.toast(get_localized_string("settings_updated"), icon="✅")
            changes.clear()  # clear changes
    with cols_save[1]:
        if st.button(get_localized_string("verify"),use_container_width = True):
            st.toast(get_localized_string("attempting_access"), icon="🔄")
            try:
                response = ask_gpt("This is a test, response 'message':'success' in json format.", model=config.MODEL[0], response_json=True, log_title='None')
                print(response)
                if response.get('message') == 'success':
                    st.toast(get_localized_string("verification_successful"), icon="✅")
                else:
                    st.toast(get_localized_string("verification_failed"), icon="❌")
            except Exception as e:
                st.toast(f"{get_localized_string('access_failed')} {e}", icon="❌")