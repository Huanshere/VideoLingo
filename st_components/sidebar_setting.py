import re
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from st_components.imports_and_utils import ask_gpt, config
import streamlit as st

def update_config(key, value):
    with open('config.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    if key == "llm_config":
        # 为 llm_config 使用特殊处理
        pattern = r'(llm_config\s*=\s*)\{.*?\}'
        replacement = f'llm_config = {repr(value)}'
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    else:
        # 单行键值对
        pattern = rf"^{re.escape(key)}\s*=.*$"
        replacement = f"{key} = {repr(value)}"
        new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    with open('config.py', 'w', encoding='utf-8') as f:
        f.write(new_content)

def page_setting():
    # st.title("🔧 VideoLingo 设置")
    
    changes = {}  # 用于存储所有更改

    st.header("LLM 配置")
    
    llm_config = config.llm_config if config.llm_config else {}
    
    api_key = st.text_input("API_key", value=llm_config.get('api_key', ''))
    base_url = st.text_input("Base_url", value=llm_config.get('base_url', ''))
    models = st.text_input("Model", value=','.join(llm_config.get('model', [])))
    new_llm_config = {
        'api_key': api_key,
        'base_url': base_url,
        'model': models.split(',') if models else []
    }
    
    if new_llm_config != config.llm_config:
        changes["llm_config"] = new_llm_config
    
    st.header("字幕设置")
    cols_audio = st.columns(2)
    with cols_audio[0]:
        audio_language = st.radio("whisper 识别语言:", options=["auto", "en"], index=0 if config.AUDIO_LANGUAGE == "auto" else 1)
        if audio_language != config.AUDIO_LANGUAGE:
            changes["AUDIO_LANGUAGE"] = audio_language
    with cols_audio[1]:
        target_language = st.text_input("翻译目标语言:", value=config.TARGET_LANGUAGE)
        if target_language != config.TARGET_LANGUAGE:
            changes["TARGET_LANGUAGE"] = target_language
    st.write("每行字幕最大字符数：")
    col1, col2 = st.columns(2)
    with col1:
        max_english_length = st.number_input("英文:", value=config.MAX_ENGLISH_LENGTH)
        if max_english_length != config.MAX_ENGLISH_LENGTH:
            changes["MAX_ENGLISH_LENGTH"] = int(max_english_length)
    
    with col2:
        max_target_language_length = st.number_input("翻译:", value=config.MAX_TARGET_LANGUAGE_LENGTH)
        if max_target_language_length != config.MAX_TARGET_LANGUAGE_LENGTH:
            changes["MAX_TARGET_LANGUAGE_LENGTH"] = int(max_target_language_length)

    resolution_options = {
        "1080p": "1920x1080",
        "480p": "854x480"
    }
    selected_resolution = st.selectbox("压制视频分辨率:", options=list(resolution_options.keys()), index=list(resolution_options.values()).index(config.RESOLUTIOM))
    resolution = resolution_options[selected_resolution]
    if resolution != config.RESOLUTIOM:
        changes["RESOLUTIOM"] = resolution

    st.header("SoVITS 角色配置")
    dubbing_character = st.text_input("配音角色:", value=config.DUBBNING_CHARACTER)
    if dubbing_character != config.DUBBNING_CHARACTER:
        changes["DUBBNING_CHARACTER"] = dubbing_character
    
    if changes:
        st.toast("记得点击下方的'保存设置'按钮", icon="🔔")
    
    st.markdown("")
    cols_save = st.columns(2)
    with cols_save[0]:
        if st.button("保    存", use_container_width = True):
            for key, value in changes.items():
                update_config(key, value)
            st.toast("设置已更新 但现阶段需要从命令行重启 streamlit 才能生效！", icon="⚠️")
            changes.clear()  # 清空更改字典
    with cols_save[1]:
        if st.button("验    证",use_container_width = True):
            st.toast("正在尝试访问...", icon="🔄")
            try:
                response = ask_gpt("this is a test, response 'code':'200' in json format.", model=llm_config.get('model')[0], response_json=True)
                if response.get('code') == '200':
                    st.toast("验证成功", icon="✅")
                else:
                    st.toast("验证失败, 请检查 api_key 和 base_url 是否正确", icon="❌")
            except Exception as e:
                st.toast(f"访问失败 {e}", icon="❌")
    st.warning("警告：目前更新设置后需要从命令行重启 streamlit 才能生效!")