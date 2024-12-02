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
    with st.expander("LLM Configuration", expanded=True):
        config_input("API_KEY", "api.key")
        config_input("BASE_URL", "api.base_url", help="Base URL for API requests")
        
        c1, c2 = st.columns([4, 1])
        with c1:
            config_input("MODEL", "api.model")
        with c2:
            if st.button("📡", key="api"):
                st.toast("API Key is valid" if check_api() else "API Key is invalid", 
                        icon="✅" if check_api() else "❌")
    
    with st.expander("Transcription and Subtitle Settings", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            langs = {
                "🇺🇸 English": "en",
                "🇨🇳 简体中文": "zh",
                "🇪🇸 Español": "es",
                "🇷🇺 Русский": "ru",
                "🇫🇷 Français": "fr",
                "🇩🇪 Deutsch": "de",
                "🇮🇹 Italiano": "it",
                "🇯🇵 日本語": "ja"
            }
            lang = st.selectbox(
                "Recognition Language:", 
                options=list(langs.keys()),
                index=list(langs.values()).index(load_key("whisper.language"))
            )
            if langs[lang] != load_key("whisper.language"):
                update_key("whisper.language", langs[lang])

        with c2:
            target_language = st.text_input("Target Language", value=load_key("target_language"))
            if target_language != load_key("target_language"):
                update_key("target_language", target_language)

        c1, c2 = st.columns(2)
        with c1:
            burn_subtitles = st.toggle("Burn Subtitles", value=load_key("resolution") != "0x0")
        
        resolution_options = {
            "1080p": "1920x1080",
            "360p": "640x360"
        }
        
        with c2:
            if burn_subtitles:
                selected_resolution = st.selectbox(
                    "Video Resolution",
                    options=list(resolution_options.keys()),
                    index=list(resolution_options.values()).index(load_key("resolution")) if load_key("resolution") != "0x0" else 0
                )
                resolution = resolution_options[selected_resolution]
            else:
                resolution = "0x0"

        if resolution != load_key("resolution"):
            update_key("resolution", resolution)
        
    with st.expander("Dubbing Settings", expanded=True):
        config_input("Max Workers", "max_workers")
        tts_methods = ["sf_fish_tts", "openai_tts", "azure_tts", "gpt_sovits", "fish_tts", "cosyvoice", "cosyvoice_cloud", "sambert"]
        selected_tts_method = st.selectbox("TTS Method", options=tts_methods, index=tts_methods.index(load_key("tts_method")))
        if selected_tts_method != load_key("tts_method"):
            update_key("tts_method", selected_tts_method)

        if selected_tts_method == "sf_fish_tts":
            config_input("SiliconFlow API Key", "sf_fish_tts.api_key")
            
            # Add mode selection dropdown
            mode_options = {
                "preset": "Preset",
                "custom": "Refer_stable",
                "dynamic": "Refer_dynamic"
            }
            selected_mode = st.selectbox(
                "Mode Selection",
                options=list(mode_options.keys()),
                format_func=lambda x: mode_options[x],
                index=list(mode_options.keys()).index(load_key("sf_fish_tts.mode")) if load_key("sf_fish_tts.mode") in mode_options.keys() else 0
            )
            if selected_mode != load_key("sf_fish_tts.mode"):
                update_key("sf_fish_tts.mode", selected_mode)
                
            if selected_mode == "preset":
                config_input("Voice", "sf_fish_tts.voice")

        elif selected_tts_method == "openai_tts":
            config_input("OpenAI Voice", "openai_tts.voice")
            config_input("OpenAI TTS API Key", "openai_tts.api_key")
            config_input("OpenAI TTS API Base URL", "openai_tts.base_url")

        elif selected_tts_method == "fish_tts":
            config_input("Fish TTS API Key", "fish_tts.api_key")
            fish_tts_character = st.selectbox("Fish TTS Character", options=list(load_key("fish_tts.character_id_dict").keys()), index=list(load_key("fish_tts.character_id_dict").keys()).index(load_key("fish_tts.character")))
            if fish_tts_character != load_key("fish_tts.character"):
                update_key("fish_tts.character", fish_tts_character)

        elif selected_tts_method == "azure_tts":
            config_input("Azure Key", "azure_tts.key")
            config_input("Azure Region", "azure_tts.region")
            config_input("Azure Voice", "azure_tts.voice")

        elif selected_tts_method == "gpt_sovits":
            st.info("配置GPT_SoVITS，请参考Github主页")
            config_input("SoVITS Character", "gpt_sovits.character")
            
            refer_mode_options = {1: "模式1：仅用提供的参考音频", 2: "模式2：仅用视频第1条语音做参考", 3: "模式3：使用视频每一条语音做参考"}
            selected_refer_mode = st.selectbox(
                "Refer Mode",
                options=list(refer_mode_options.keys()),
                format_func=lambda x: refer_mode_options[x],
                index=list(refer_mode_options.keys()).index(load_key("gpt_sovits.refer_mode")),
                help="配置GPT-SoVITS的参考音频模式"
            )
            if selected_refer_mode != load_key("gpt_sovits.refer_mode"):
                update_key("gpt_sovits.refer_mode", selected_refer_mode)
        elif selected_tts_method == "cosyvoice":
            config_input("API URL", "cosyvoice.api_url")
            speakers = ["中文男","中文女","英文男","英文女","粤语女","日语男","韩语女"]
            speaker = st.selectbox("发音人", options=speakers, index=speakers.index(load_key("cosyvoice.speaker")))
            if speaker != load_key("cosyvoice.speaker"):
                update_key("cosyvoice.speaker", speaker)
            config_input("语速", "cosyvoice.speed")
        elif selected_tts_method == "cosyvoice_cloud":
            config_input("API KEY", "cosyvoice_cloud.api_key", help="Dashscope API KEY")
            speakers = ["longwan","longcheng","longhua","longxiaochun","longxiaoxia","longxiaocheng","longxiaobai",
            "longlaotie","longshu","longshuo","longjing","longmiao","longyue","longyuan","longfei","longjielidou",
            "longtong","longxiang","loongstella","loongbella"]
            speaker = st.selectbox("发音人", options=speakers, index=speakers.index(load_key("cosyvoice_cloud.speaker")), help="可以在 https://help.aliyun.com/zh/model-studio/developer-reference/timbre-list 查看不同发音人效果")
            if speaker != load_key("cosyvoice_cloud.speaker"):
                update_key("cosyvoice_cloud.speaker", speaker)
            config_input("语速", "cosyvoice_cloud.speed")
        elif selected_tts_method == "sambert":
            st.info("Sambert语音合成API基于达摩院改良的自回归韵律模型，支持文本至语音的实时流式合成。")
            speakers = ["sambert-zhinan-v1","sambert-zhiqi-v1","sambert-zhichu-v1","sambert-zhide-v1","sambert-zhijia-v1",
            "sambert-zhiru-v1","sambert-zhiqian-v1","sambert-zhixiang-v1","sambert-zhiwei-v1",
            "sambert-zhihao-v1","sambert-zhijing-v1","sambert-zhiming-v1","sambert-zhimo-v1",
            "sambert-zhina-v1","sambert-zhishu-v1","sambert-zhistella-v1","sambert-zhiting-v1",
            "sambert-zhixiao-v1","sambert-zhiya-v1","sambert-zhiye-v1","sambert-zhiying-v1",
            "sambert-zhiyuan-v1","sambert-zhiyue-v1","sambert-zhigui-v1","sambert-zhishuo-v1",
            "sambert-zhimiao-emo-v1","sambert-zhimao-v1","sambert-zhilun-v1","sambert-zhifei-v1",
            "sambert-zhida-v1","sambert-camila-v1","sambert-perla-v1","sambert-indah-v1","sambert-clara-v1",
            "sambert-hanna-v1","sambert-beth-v1","sambert-betty-v1","sambert-cally-v1","sambert-cindy-v1",
            "sambert-eva-v1","sambert-donna-v1","sambert-brian-v1","sambert-waan-v1"]
            config_input("API KEY", "sambert.api_key", help="Dashscope API KEY")
            # config_input("音色", "sambert.speaker")
            speaker = st.selectbox("发音人", options=speakers, index=speakers.index(load_key("sambert.speaker")),
                help="访问 https://help.aliyun.com/zh/model-studio/developer-reference/model-list 查看不同说话人特性")
            if speaker != load_key("sambert.speaker"):
                update_key("sambert.speaker", speaker)
            

def check_api():
    try:
        resp = ask_gpt("This is a test, response 'message':'success' in json format.", 
                      response_json=True, log_title='None')
        return resp.get('message') == 'success'
    except Exception:
        return False