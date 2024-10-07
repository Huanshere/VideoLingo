import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from st_components.imports_and_utils import ask_gpt
import streamlit as st
from i18n.st_i18n import get_system_language
from i18n.st_i18n import get_localized_string as gls
import time
import requests
from core.config_utils import update_key, load_key

def init_display_language():
    if load_key("display_language") == "auto":
        display_language = get_system_language()
        update_key("display_language", display_language)
        time.sleep(0.2)
        st.rerun()

def page_setting():
    init_display_language()

    with st.expander(gls("llm_config"), expanded=True):

        api_key = st.text_input("API_KEY", value=load_key("api.key"))
        if api_key != load_key("api.key"):
            update_key("api.key", api_key)

        selected_base_url = st.text_input("BASE_URL", value=load_key("api.base_url"), help=gls("base_url_help"))
        if selected_base_url != load_key("api.base_url"):
            update_key("api.base_url", selected_base_url)

        col1, col2 = st.columns([4, 1])
        with col1:
            model = st.text_input("MODEL", value=load_key("api.model"))
            if model and model != load_key("api.model"):
                update_key("api.model", model)
        with col2:
            if st.button("📡", key="api"):
                if valid_llm_api():
                    st.toast("API Key is valid", icon="✅")
                else:
                    st.toast("API Key is invalid", icon="❌")
    
    with st.expander(gls("subtitle_settings"), expanded=True):
        whisper_method_options = ["whisperX 💻", "whisperX ☁️"]
        whisper_method_mapping = {"whisperX 💻": "whisperx", "whisperX ☁️": "whisperxapi"}
        selected_whisper_method_display = st.selectbox(gls("whisper_method"), options=whisper_method_options, index=whisper_method_options.index("whisperX 💻" if load_key("whisper.method") == "whisperx" else "whisperX ☁️"))
        selected_whisper_method = whisper_method_mapping[selected_whisper_method_display]
        if selected_whisper_method != load_key("whisper.method"):
            update_key("whisper.method", selected_whisper_method)

        if selected_whisper_method == "whisperx":
            uvr_before_transcription = st.toggle(gls("uvr_before_transcription"), value=load_key("whisper.uvr_before_transcription"), help=gls("uvr_before_transcription_help"))
            if uvr_before_transcription != load_key("whisper.uvr_before_transcription"):
                update_key("whisper.uvr_before_transcription", uvr_before_transcription)
        elif selected_whisper_method == "whisperxapi":    
            col1, col2 = st.columns([4, 1])
            with col1:
                replicate_api_token = st.text_input(gls("replicate_api_token"), value=load_key("replicate_api_token"), help=gls("replicate_api_token_help"))
                if replicate_api_token != load_key("replicate_api_token"):
                    update_key("replicate_api_token", replicate_api_token)
            with col2:
                if st.button("📡", key="replicate"):
                    if valid_replicate_token(replicate_api_token):
                        st.toast("Replicate API Token is valid", icon="✅")
                    else:
                        st.toast("Replicate API Token is invalid", icon="❌")
            
        col1, col2 = st.columns(2)
        with col1:
            whisper_language_options = ["en", "zh", "auto"]
            selected_whisper_language = st.selectbox(gls("whisper_language"), options=whisper_language_options, index=whisper_language_options.index(load_key("whisper.language")))
            if selected_whisper_language != load_key("whisper.language"):
                update_key("whisper.language", selected_whisper_language)

        with col2:
            target_language = st.text_input(gls("translation_target_language"), value=load_key("target_language") , help=gls("translation_target_language_help"))
            if target_language != load_key("target_language"):
                update_key("target_language", target_language)

        include_video = st.toggle(gls("include_video"), value=load_key("resolution") != "0x0")

        resolution_options = {
            "1080p": "1920x1080",
            "360p": "640x360"
        }
        selected_resolution = st.selectbox(
            gls("video_resolution"),
            options=list(resolution_options.keys()),
            index=list(resolution_options.values()).index(load_key("resolution")) if load_key("resolution") != "0x0" else 0,
            disabled=not include_video
        )

        if include_video:
            resolution = resolution_options[selected_resolution]
        else:
            resolution = "0x0"

        if resolution != load_key("resolution"):
            update_key("resolution", resolution)
        
    with st.expander(gls("dubbing_settings"), expanded=False):
        tts_methods = ["openai_tts", "azure_tts", "gpt_sovits", "fish_tts"]
        selected_tts_method = st.selectbox(gls("tts_method"), options=tts_methods, index=tts_methods.index(load_key("tts_method")))
        if selected_tts_method != load_key("tts_method"):
            update_key("tts_method", selected_tts_method)

        if selected_tts_method == "openai_tts":
            oai_voice = st.text_input(gls("openai_voice"), value=load_key("openai_tts.voice"))
            if oai_voice != load_key("openai_tts.voice"):
                update_key("openai_tts.voice", oai_voice)

            oai_tts_api_key = st.text_input(gls("openai_tts_api_key"), value=load_key("openai_tts.api_key"))
            if oai_tts_api_key != load_key("openai_tts.api_key"):
                update_key("openai_tts.api_key", oai_tts_api_key)

            oai_api_base_url = st.text_input(gls("openai_tts_api_base_url"), value=load_key("openai_tts.base_url"))
            if oai_api_base_url != load_key("openai_tts.base_url"):
                update_key("openai_tts.base_url", oai_api_base_url)

        elif selected_tts_method == "fish_tts":
            fish_tts_api_key = st.text_input(gls("fish_tts_api_key"), value=load_key("fish_tts.api_key"))
            if fish_tts_api_key != load_key("fish_tts.api_key"):
                update_key("fish_tts.api_key", fish_tts_api_key)

            fish_tts_character = st.selectbox(gls("fish_tts_character"), options=list(load_key("fish_tts.character_id_dict").keys()), index=list(load_key("fish_tts.character_id_dict").keys()).index(load_key("fish_tts.character")))
            if fish_tts_character != load_key("fish_tts.character"):
                update_key("fish_tts.character", fish_tts_character)

        elif selected_tts_method == "azure_tts":
            azure_key = st.text_input(gls("azure_key"), value=load_key("azure_tts.key"))
            if azure_key != load_key("azure_tts.key"):
                update_key("azure_tts.key", azure_key)

            azure_region = st.text_input(gls("azure_region"), value=load_key("azure_tts.region"))
            if azure_region != load_key("azure_tts.region"):
                update_key("azure_tts.region", azure_region)

            azure_voice = st.text_input(gls("azure_voice"), value=load_key("azure_tts.voice"))
            if azure_voice != load_key("azure_tts.voice"):
                update_key("azure_tts.voice", azure_voice)

        elif selected_tts_method == "gpt_sovits":
            st.info("配置GPT_SoVITS，请参考Github主页")
            sovits_character = st.text_input(gls("sovits_character"), value=load_key("gpt_sovits.character"))
            if sovits_character != load_key("gpt_sovits.character"):
                update_key("gpt_sovits.character", sovits_character)
            
            refer_mode_options = {1: "模式1：仅用提供的参考音频", 2: "模式2：仅用视频第1条语音做参考", 3: "模式3：使用视频每一条语音做参考"}
            selected_refer_mode = st.selectbox(
                gls("refer_mode"),
                options=list(refer_mode_options.keys()),
                format_func=lambda x: refer_mode_options[x],
                index=list(refer_mode_options.keys()).index(load_key("gpt_sovits.refer_mode")),
                help="配置GPT-SoVITS的参考音频模式"
            )
            if selected_refer_mode != load_key("gpt_sovits.refer_mode"):
                update_key("gpt_sovits.refer_mode", selected_refer_mode)

        original_volume_options = {gls("mute"): 0, "10%": 0.1}

        selected_original_volume = st.selectbox(
            gls("original_volume"),
            options=list(original_volume_options.keys()),
            index=list(original_volume_options.values()).index(load_key("original_volume"))
        )
        if original_volume_options[selected_original_volume] != load_key("original_volume"):
            update_key("original_volume", original_volume_options[selected_original_volume])

    language_mapping = {"中文": "zh_CN", "English": "en_US"}
    current_display = next((k for k, v in language_mapping.items() if v == load_key("display_language")), "en_US")
    language_options = list(language_mapping.keys())
    selected_display_language = st.selectbox("🌍 Language 语言", options=language_options, index=language_options.index(current_display))
    if language_mapping[selected_display_language] != load_key("display_language"):
        update_key("display_language", language_mapping[selected_display_language])
        time.sleep(0.2)
        st.rerun()
            

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
