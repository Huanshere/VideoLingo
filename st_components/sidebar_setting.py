import re
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from st_components.imports_and_utils import ask_gpt
import config
import streamlit as st
from st_components.i18n import get_system_language
from st_components.i18n import get_localized_string as gls
import time
import requests

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

    with st.expander(gls("llm_config"), expanded=True):

        api_key = st.text_input("API_KEY", value=config.API_KEY)
        if api_key != config.API_KEY:
            changes["API_KEY"] = api_key

        selected_base_url = st.text_input("BASE_URL", value=config.BASE_URL, help=gls("base_url_help"))
        if selected_base_url != config.BASE_URL:
            changes["BASE_URL"] = selected_base_url

        model = st.text_input("MODEL", value=config.MODEL)
        if model and model != config.MODEL:
            changes["MODEL"] = model
    
    with st.expander(gls("subtitle_settings"), expanded=True):
        whisper_method_options = ["whisperX 💻", "whisperX ☁️"]
        whisper_method_mapping = {"whisperX 💻": "whisperx", "whisperX ☁️": "whisperxapi"}
        selected_whisper_method_display = st.selectbox(gls("whisper_method"), options=whisper_method_options, index=whisper_method_options.index("whisperX 💻" if config.WHISPER_METHOD == "whisperx" else "whisperX ☁️"))
        selected_whisper_method = whisper_method_mapping[selected_whisper_method_display]
        if selected_whisper_method != config.WHISPER_METHOD:
            changes["WHISPER_METHOD"] = selected_whisper_method
        if selected_whisper_method == "whisperxapi":    
            replicate_api_token = st.text_input(gls("replicate_api_token"), value=config.REPLICATE_API_TOKEN, help=gls("replicate_api_token_help"))
            if replicate_api_token != config.REPLICATE_API_TOKEN:
                changes["REPLICATE_API_TOKEN"] = replicate_api_token
            
        col1, col2 = st.columns(2)
        with col1:
            whisper_language_options = ["en", "zh", "auto"]
            selected_whisper_language = st.selectbox(gls("whisper_language"), options=whisper_language_options, index=whisper_language_options.index(config.WHISPER_LANGUAGE))
            if selected_whisper_language != config.WHISPER_LANGUAGE:
                changes["WHISPER_LANGUAGE"] = selected_whisper_language

        with col2:
            target_language = st.text_input(gls("translation_target_language"), value=config.TARGET_LANGUAGE, help=gls("translation_target_language_help"))
            if target_language != config.TARGET_LANGUAGE:
                changes["TARGET_LANGUAGE"] = target_language

        resolution_options = {
            "1080p": "1920x1080",
            "360p": "640x360",
            "No video": "0x0"
        }
        selected_resolution = st.selectbox(gls("video_resolution"), options=list(resolution_options.keys()), index=list(resolution_options.values()).index(config.RESOLUTION))
        resolution = resolution_options[selected_resolution]
        if resolution != config.RESOLUTION:
            changes["RESOLUTION"] = resolution
        
    with st.expander(gls("dubbing_settings"), expanded=True):
        tts_methods = ["openai", "azure_tts", "gpt_sovits", "fish_tts"]
        selected_tts_method = st.selectbox(gls("tts_method"), options=tts_methods, index=tts_methods.index(config.TTS_METHOD))
        if selected_tts_method != config.TTS_METHOD:
            changes["TTS_METHOD"] = selected_tts_method

        if selected_tts_method == "openai":
            oai_voice = st.text_input(gls("openai_voice"), value=config.OAI_VOICE)
            if oai_voice != config.OAI_VOICE:
                changes["OAI_VOICE"] = oai_voice

            oai_tts_api_key = st.text_input(gls("openai_tts_api_key"), value=config.OAI_TTS_API_KEY)
            if oai_tts_api_key != config.OAI_TTS_API_KEY:
                changes["OAI_TTS_API_KEY"] = oai_tts_api_key

            oai_tts_api_base_url = st.text_input(gls("openai_tts_api_base_url"), value=config.OAI_TTS_API_BASE_URL)
            if oai_tts_api_base_url != config.OAI_TTS_API_BASE_URL:
                changes["OAI_TTS_API_BASE_URL"] = oai_tts_api_base_url

        elif selected_tts_method == "fish_tts":
            fish_tts_api_key = st.text_input(gls("fish_tts_api_key"), value=config.FISH_TTS_API_KEY)
            if fish_tts_api_key != config.FISH_TTS_API_KEY:
                changes["FISH_TTS_API_KEY"] = fish_tts_api_key

            fish_tts_character = st.selectbox(gls("fish_tts_character"), options=list(config.FISH_TTS_CHARACTER_ID_DICT.keys()), index=list(config.FISH_TTS_CHARACTER_ID_DICT.keys()).index(config.FISH_TTS_CHARACTER))
            if fish_tts_character != config.FISH_TTS_CHARACTER:
                changes["FISH_TTS_CHARACTER"] = fish_tts_character

        elif selected_tts_method == "azure_tts":
            azure_key = st.text_input(gls("azure_key"), value=config.AZURE_KEY)
            if azure_key != config.AZURE_KEY:
                changes["AZURE_KEY"] = azure_key

            azure_region = st.text_input(gls("azure_region"), value=config.AZURE_REGION)
            if azure_region != config.AZURE_REGION:
                changes["AZURE_REGION"] = azure_region

            azure_voice = st.text_input(gls("azure_voice"), value=config.AZURE_VOICE)
            if azure_voice != config.AZURE_VOICE:
                changes["AZURE_VOICE"] = azure_voice
        elif selected_tts_method == "gpt_sovits":
            st.info("配置GPT_SoVITS，参考[安装指南](https://github.com/Huanshere/VideoLingo/blob/main/docs/install_locally_zh.md)")
            st.warning("注意：当前适配只支持输出为中文，输入参考为英文。对于嘈杂音频效果不佳，且偶尔会发生漏句漏字现象。如使用参考视频语音的模式，建议选用和视频原声音色相近的底模")
            sovits_character = st.text_input(gls("sovits_character"), value=config.DUBBING_CHARACTER, help="需在 GPT-SoVITS 的 config 目录下配置有 `xxx.yaml` 文件")
            if sovits_character != config.DUBBING_CHARACTER:
                changes["DUBBING_CHARACTER"] = sovits_character
            
            refer_mode_options = {1: "模式1：仅用提供的参考音频", 2: "模式2：仅用视频第1条语音做参考", 3: "模式3：使用视频每一条语音做参考"}
            selected_refer_mode = st.selectbox(
                gls("refer_mode"),
                options=list(refer_mode_options.keys()),
                format_func=lambda x: refer_mode_options[x],
                index=list(refer_mode_options.keys()).index(config.REFER_MODE),
                help="配置GPT-SoVITS的参考音频模式"
            )
            if selected_refer_mode != config.REFER_MODE:
                changes["REFER_MODE"] = selected_refer_mode

        original_volume_options = {gls("mute"): 0, "10%": 0.1}

        selected_original_volume = st.selectbox(
            gls("original_volume"),
            options=list(original_volume_options.keys()),
            index=list(original_volume_options.values()).index(config.ORIGINAL_VOLUME)
        )
        if original_volume_options[selected_original_volume] != config.ORIGINAL_VOLUME:
            changes["ORIGINAL_VOLUME"] = original_volume_options[selected_original_volume]

    display_language_options = ["中文", "English", "Auto"]
    display_language_mapping = {"中文": "zh_CN", "English": "en_US", "Auto": "auto"}
    current_display = next((k for k, v in display_language_mapping.items() if v == config.DISPLAY_LANGUAGE), "Auto")
    selected_display_language = st.selectbox(gls("display_language"), options=display_language_options, index=display_language_options.index(current_display))
    if display_language_mapping[selected_display_language] != config.DISPLAY_LANGUAGE:
        changes["DISPLAY_LANGUAGE"] = display_language_mapping[selected_display_language]

    if changes:
        st.toast(gls("remember_save_settings"), icon="🔔")
    
    st.markdown("")
    cols_save = st.columns(2)
    with cols_save[0]:
        if st.button(gls("save"), use_container_width = True):
            for key, value in changes.items():
                update_config(key, value)
            st.toast(gls("settings_updated"), icon="✅")
            changes.clear()  # clear changes
    with cols_save[1]:
        if st.button(gls("verify"), use_container_width=True):
            st.toast(gls("attempting_access"), icon="🔄")
            if valid_llm_api():
                st.toast(f"LLM API 验证成功", icon="✅")
            else:
                st.toast(f"LLM API 验证失败", icon="❌")
            
            if config.WHISPER_METHOD == "whisperxapi":
                if valid_replicate_token(config.REPLICATE_API_TOKEN):
                    st.toast(f"Replicate Token 验证成功", icon="✅")
                else:
                    st.toast(f"Replicate Token 验证失败", icon="❌")
            

def valid_llm_api():
    try:
        response = ask_gpt("This is a test, response 'message':'success' in json format.", response_json=True, log_title='None')
        return response.get('message') == 'success'
    except Exception:
        return False

def valid_replicate_token(token):
    url = "https://api.replicate.com/v1/predictions"
    headers = {"Authorization": f"Token {token}"}
    response = requests.get(url, headers=headers)
    return response.status_code == 200
