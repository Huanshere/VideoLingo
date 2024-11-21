import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from st_components.imports_and_utils import ask_gpt
import streamlit as st
from core.config_utils import update_key, load_key

def config_input(label, key, help=None):
    """Generic config input handler"""
    val = st.text_input(
        label, 
        value=load_key(key), 
        help=help,
        key=f"config_input_{key}"
    )
    if val != load_key(key):
        update_key(key, val)
    return val

def page_setting():
    # LLM Configuration 部分
    st.subheader("LLM Configuration")
    
    # 模型配置管理
    st.subheader("Model Configurations")
    
    # 获取现有模型列表
    models = load_key("llm_models")
    
    # 添加新模型按钮
    if st.button("➕ Add New Model"):
        new_model_name = f"model_{len(models)}"
        update_key(f"llm_models.{new_model_name}", {
            "key": "",
            "base_url": "",
            "model": ""
        })
        st.rerun()

    # 显示现有模型配置
    for model_name in models:
        st.markdown(f"### 📑 {model_name}")
        # 模型名称编辑（可选）
        new_name = st.text_input("Model Name", value=model_name, key=f"name_{model_name}")
        
        # 基础配置
        config_input(f"API Key", f"llm_models.{model_name}.key")
        config_input(f"Base URL", f"llm_models.{model_name}.base_url")
        config_input(f"Model", f"llm_models.{model_name}.model")
        
        # 测试和删除按钮
        c1, c2, c3 = st.columns([3, 1, 1])
        with c2:
            if st.button("🔍 Test", key=f"test_{model_name}"):
                api_set = load_key(f"llm_models.{model_name}")
                st.toast(
                    "API Key is valid" if check_api(api_set) else "API Key is invalid",
                    icon="✅" if check_api(api_set) else "❌"
                )
        with c3:
            if len(models) > 1 and st.button("🗑️ Delete", key=f"delete_{model_name}"):
                models_dict = load_key("llm_models")
                del models_dict[model_name]
                update_key("llm_models", models_dict)
                st.rerun()
        st.divider()

    # 阶段配置
    st.subheader("Stage Configurations")
    stages = {
        "align": "Subtitle Alignment",
        "split": "Subtitle Splitting",
        "summarize": "Summarization",
        "translate_faithfulness": "Translation (Accurate)",
        "translate_expressiveness": "Translation (Elegant)",
        "reduce": "Subtitle Reduction"
    }
    
    for stage_key, stage_name in stages.items():
        col1, col2 = st.columns([3, 2])
        with col1:
            st.write(stage_name)
        with col2:
            current_model = load_key(f"llm_stages.{stage_key}")
            selected_model = st.selectbox(
                "Model",
                options=list(models.keys()),
                index=list(models.keys()).index(current_model),
                key=f"stage_{stage_key}",
                label_visibility="collapsed"
            )
            if selected_model != current_model:
                update_key(f"llm_stages.{stage_key}", selected_model)
      
    # Transcription and Subtitle Settings 部分
    st.subheader("Transcription and Subtitle Settings")
    
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
    
    # Dubbing Settings 部分
    st.subheader("Dubbing Settings")
    
    tts_methods = ["sf_fish_tts", "openai_tts", "azure_tts", "gpt_sovits", "fish_tts"]
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

def check_api(api_set):
    """检查API配置是否有效"""
    try:
        resp = ask_gpt(
            "This is a test, response 'message':'success' in json format.",
            response_json=True,
            log_title='None',
            check_api=True,
            api_set=api_set
        )
        return resp.get('message') == 'success'
    except Exception:
        return False