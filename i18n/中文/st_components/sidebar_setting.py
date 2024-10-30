import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from st_components.imports_and_utils import ask_gpt
import streamlit as st
from core.config_utils import update_key, load_key
import requests

def page_setting():
    with st.expander("LLM 配置", expanded=True):
        api_key = st.text_input("API_KEY", value=load_key("api.key"))
        if api_key != load_key("api.key"):
            update_key("api.key", api_key)

        selected_base_url = st.text_input("BASE_URL", value=load_key("api.base_url"), help="API请求的基础URL")
        if selected_base_url != load_key("api.base_url"):
            update_key("api.base_url", selected_base_url)

        col1, col2 = st.columns([4, 1])
        with col1:
            model = st.text_input("模型", value=load_key("api.model"))
            if model and model != load_key("api.model"):
                update_key("api.model", model)
        with col2:
            if st.button("📡", key="api"):
                if valid_llm_api():
                    st.toast("API密钥有效", icon="✅")
                else:
                    st.toast("API密钥无效", icon="❌")
    
    with st.expander("转写和字幕设置", expanded=True):
        whisper_method_options = ["whisperX 💻", "whisperX ☁️"]
        whisper_method_mapping = {"whisperX 💻": "whisperx", "whisperX ☁️": "whisperxapi"}
        selected_whisper_method_display = st.selectbox("Whisper方法:", options=whisper_method_options, index=whisper_method_options.index("whisperX 💻" if load_key("whisper.method") == "whisperx" else "whisperX ☁️"))
        selected_whisper_method = whisper_method_mapping[selected_whisper_method_display]
        if selected_whisper_method != load_key("whisper.method"):
            update_key("whisper.method", selected_whisper_method)
            
        if selected_whisper_method == "whisperxapi":    
            col1, col2 = st.columns([4, 1])
            with col1:
                replicate_api_token = st.text_input("Replicate API令牌", value=load_key("replicate_api_token"), help="Replicate API令牌")
                if replicate_api_token != load_key("replicate_api_token"):
                    update_key("replicate_api_token", replicate_api_token)
            with col2:
                if st.button("📡", key="replicate"):
                    if valid_replicate_token(replicate_api_token):
                        st.toast("Replicate API令牌有效", icon="✅")
                    else:
                        st.toast("Replicate API令牌无效", icon="❌")
            
        col1, col2 = st.columns(2)
        with col1:
            whisper_language_options_dict = {
            "🇺🇸 英语": "en",
            "🇨🇳 中文": "zh", 
            "🇷🇺 俄语": "ru",
            "🇫🇷 法语": "fr",
            "🇩🇪 德语": "de",
            "🇮🇹 意大利语": "it",
            "🇪🇸 西班牙语": "es",
            "🇯🇵 日语": "ja"
            }
            selected_whisper_language = st.selectbox(
                "识别语言:", 
                options=list(whisper_language_options_dict.keys()),
                index=list(whisper_language_options_dict.values()).index(load_key("whisper.language"))
            )
            if whisper_language_options_dict[selected_whisper_language] != load_key("whisper.language"):
                update_key("whisper.language", whisper_language_options_dict[selected_whisper_language])

        with col2:
            target_language = st.text_input("翻译目标语言", value=load_key("target_language") , help="翻译目标语言")
            if target_language != load_key("target_language"):
                update_key("target_language", target_language)

        include_video = st.toggle("包含视频", value=load_key("resolution") != "0x0")

        resolution_options = {
            "1080p": "1920x1080",
            "360p": "640x360"
        }
        selected_resolution = st.selectbox(
            "视频分辨率",
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
        
    with st.expander("配音设置", expanded=False):
        tts_methods = ["openai_tts", "azure_tts", "gpt_sovits", "fish_tts"]
        selected_tts_method = st.selectbox("TTS方法", options=tts_methods, index=tts_methods.index(load_key("tts_method")))
        if selected_tts_method != load_key("tts_method"):
            update_key("tts_method", selected_tts_method)

        if selected_tts_method == "openai_tts":
            oai_voice = st.text_input("OpenAI语音", value=load_key("openai_tts.voice"))
            if oai_voice != load_key("openai_tts.voice"):
                update_key("openai_tts.voice", oai_voice)

            oai_tts_api_key = st.text_input("OpenAI TTS API密钥", value=load_key("openai_tts.api_key"))
            if oai_tts_api_key != load_key("openai_tts.api_key"):
                update_key("openai_tts.api_key", oai_tts_api_key)

            oai_api_base_url = st.text_input("OpenAI TTS API基础URL", value=load_key("openai_tts.base_url"))
            if oai_api_base_url != load_key("openai_tts.base_url"):
                update_key("openai_tts.base_url", oai_api_base_url)

        elif selected_tts_method == "fish_tts":
            fish_tts_api_key = st.text_input("Fish TTS API密钥", value=load_key("fish_tts.api_key"))
            if fish_tts_api_key != load_key("fish_tts.api_key"):
                update_key("fish_tts.api_key", fish_tts_api_key)

            fish_tts_character = st.selectbox("Fish TTS角色", options=list(load_key("fish_tts.character_id_dict").keys()), index=list(load_key("fish_tts.character_id_dict").keys()).index(load_key("fish_tts.character")))
            if fish_tts_character != load_key("fish_tts.character"):
                update_key("fish_tts.character", fish_tts_character)

        elif selected_tts_method == "azure_tts":
            azure_key = st.text_input("Azure密钥", value=load_key("azure_tts.key"))
            if azure_key != load_key("azure_tts.key"):
                update_key("azure_tts.key", azure_key)

            azure_region = st.text_input("Azure区域", value=load_key("azure_tts.region"))
            if azure_region != load_key("azure_tts.region"):
                update_key("azure_tts.region", azure_region)

            azure_voice = st.text_input("Azure语音", value=load_key("azure_tts.voice"))
            if azure_voice != load_key("azure_tts.voice"):
                update_key("azure_tts.voice", azure_voice)

        elif selected_tts_method == "gpt_sovits":
            st.info("配置GPT_SoVITS，请参考Github主页")
            sovits_character = st.text_input("SoVITS角色", value=load_key("gpt_sovits.character"))
            if sovits_character != load_key("gpt_sovits.character"):
                update_key("gpt_sovits.character", sovits_character)
            
            refer_mode_options = {1: "模式1：仅用提供的参考音频", 2: "模式2：仅用视频第1条语音做参考", 3: "模式3：使用视频每一条语音做参考"}
            selected_refer_mode = st.selectbox(
                "参考模式",
                options=list(refer_mode_options.keys()),
                format_func=lambda x: refer_mode_options[x],
                index=list(refer_mode_options.keys()).index(load_key("gpt_sovits.refer_mode")),
                help="配置GPT-SoVITS的参考音频模式"
            )
            if selected_refer_mode != load_key("gpt_sovits.refer_mode"):
                update_key("gpt_sovits.refer_mode", selected_refer_mode)

        original_volume_options = {"静音": 0, "10%": 0.1}

        selected_original_volume = st.selectbox(
            "原始音量",
            options=list(original_volume_options.keys()),
            index=list(original_volume_options.values()).index(load_key("original_volume"))
        )
        if original_volume_options[selected_original_volume] != load_key("original_volume"):
            update_key("original_volume", original_volume_options[selected_original_volume])

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
