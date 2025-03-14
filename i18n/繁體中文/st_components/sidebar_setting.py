import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from st_components.imports_and_utils import ask_gpt
import streamlit as st
from core.config_utils import update_key, load_key

def config_input(label, key, help=None):
    """Generic config input handler"""
    val = st.text_input(label, value=load_key(key), help=help)
    if val != load_key(key):
        update_key(key, val)
    return val

def page_setting():
    with st.expander("LLM 配置", expanded=True):
        config_input("API_KEY", "api.key")
        config_input("BASE_URL", "api.base_url", help="Openai 格式，將自動添加 /v1/chat/completions")
        
        c1, c2 = st.columns([4, 1])
        with c1:
            config_input("模型", "api.model", help="點擊右側按鈕檢查 API 有效性")
        with c2:
            if st.button("📡", key="api"):
                st.toast("API 密鑰有效" if check_api() else "API 密鑰無效", 
                        icon="✅" if check_api() else "❌")
    
    with st.expander("轉寫和字幕設置", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            langs = {
                "🇺🇸 English": "en",
                "🇨🇳 簡體中文": "zh",
                "🇪🇸 Español": "es",
                "🇷🇺 Русский": "ru",
                "🇫🇷 Français": "fr",
                "🇩🇪 Deutsch": "de",
                "🇮🇹 Italiano": "it",
                "🇯🇵 日本語": "ja"
            }
            lang = st.selectbox(
                "識別語言:", 
                options=list(langs.keys()),
                index=list(langs.values()).index(load_key("whisper.language"))
            )
            if langs[lang] != load_key("whisper.language"):
                update_key("whisper.language", langs[lang])

        with c2:
            target_language = st.text_input("目標語言", value=load_key("target_language"))
            if target_language != load_key("target_language"):
                update_key("target_language", target_language)

        demucs = st.toggle("人聲分離增強", value=load_key("demucs"), help="推薦用於背景噪音較大的視頻，但會增加處理時間")
        if demucs != load_key("demucs"):
            update_key("demucs", demucs)

        burn_subtitles = st.toggle("壓制字幕", value=load_key("resolution") != "0x0", help="需要更長處理時間")
        
        resolution_options = {
            "1080p": "1920x1080",
            "360p": "640x360"
        }
            
        if burn_subtitles:
            selected_resolution = st.selectbox(
                "視頻分辨率",
                options=list(resolution_options.keys()),
                index=list(resolution_options.values()).index(load_key("resolution")) if load_key("resolution") != "0x0" else 0
            )
            resolution = resolution_options[selected_resolution]
        else:
            resolution = "0x0"

        if resolution != load_key("resolution"):
            update_key("resolution", resolution)
        
    with st.expander("配音設置", expanded=True):
        tts_methods = ["azure_tts", "openai_tts", "fish_tts", "sf_fish_tts", "edge_tts", "gpt_sovits", "custom_tts"]
        select_tts = st.selectbox("TTS 方法", options=tts_methods, index=tts_methods.index(load_key("tts_method")))
        if select_tts != load_key("tts_method"):
            update_key("tts_method", select_tts)

        # sub settings for each tts method
        if select_tts == "sf_fish_tts":
            config_input("SiliconFlow API 密鑰", "sf_fish_tts.api_key")
            
            # Add mode selection dropdown
            mode_options = {
                "preset": "預設",
                "custom": "clone(stable)",
                "dynamic": "clone(dynamic)"
            }
            selected_mode = st.selectbox(
                "模式選擇",
                options=list(mode_options.keys()),
                format_func=lambda x: mode_options[x],
                index=list(mode_options.keys()).index(load_key("sf_fish_tts.mode")) if load_key("sf_fish_tts.mode") in mode_options.keys() else 0
            )
            if selected_mode != load_key("sf_fish_tts.mode"):
                update_key("sf_fish_tts.mode", selected_mode)
                
            if selected_mode == "preset":
                config_input("語音", "sf_fish_tts.voice")

        elif select_tts == "openai_tts":
            config_input("302ai API", "openai_tts.api_key")
            config_input("OpenAI 語音", "openai_tts.voice")

        elif select_tts == "fish_tts":
            config_input("302ai API", "fish_tts.api_key")
            fish_tts_character = st.selectbox("Fish TTS 角色", options=list(load_key("fish_tts.character_id_dict").keys()), index=list(load_key("fish_tts.character_id_dict").keys()).index(load_key("fish_tts.character")))
            if fish_tts_character != load_key("fish_tts.character"):
                update_key("fish_tts.character", fish_tts_character)

        elif select_tts == "azure_tts":
            config_input("302ai API", "azure_tts.api_key")
            config_input("Azure 語音", "azure_tts.voice")
        
        elif select_tts == "gpt_sovits":
            st.info("配置 GPT_SoVITS，請參考 Github 主頁")
            config_input("SoVITS 角色", "gpt_sovits.character")
            
            refer_mode_options = {1: "模式1：僅用提供的參考音頻", 2: "模式2：僅用視頻第1條語音做參考", 3: "模式3：使用視頻每一條語音做參考"}
            selected_refer_mode = st.selectbox(
                "參考模式",
                options=list(refer_mode_options.keys()),
                format_func=lambda x: refer_mode_options[x],
                index=list(refer_mode_options.keys()).index(load_key("gpt_sovits.refer_mode")),
                help="配置 GPT-SoVITS 的參考音頻模式"
            )
            if selected_refer_mode != load_key("gpt_sovits.refer_mode"):
                update_key("gpt_sovits.refer_mode", selected_refer_mode)
        elif select_tts == "edge_tts":
            config_input("Edge TTS 語音", "edge_tts.voice")

def check_api():
    try:
        resp = ask_gpt("This is a test, response 'message':'success' in json format.", 
                      response_json=True, log_title='None')
        return resp.get('message') == 'success'
    except Exception:
        return False
