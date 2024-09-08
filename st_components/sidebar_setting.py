import re
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from st_components.imports_and_utils import ask_gpt
import config
import streamlit as st

def update_config(key, value):
    with open('config.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    pattern = rf"^{re.escape(key)}\s*=.*$"
    replacement = f"{key} = {repr(value)}"
    new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    with open('config.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
def page_setting():
    changes = {}  # 用于存储所有更改

    st.header("LLM 配置")
    
    api_key = st.text_input("API_KEY", value=config.API_KEY)
    if api_key != config.API_KEY:
        changes["API_KEY"] = api_key

    selected_base_url = st.text_input("BASE_URL", value=config.BASE_URL)
    if selected_base_url != config.BASE_URL:
        changes["BASE_URL"] = selected_base_url
    
    st.header("字幕设置")
    # select WHISPER_METHOD = 'whisperx'
    whisper_method_options = ["whisperx", "whisperxapi", "whisper_timestamped"]
    selected_whisper_method = st.selectbox("Whisper Method:", options=whisper_method_options, index=whisper_method_options.index(config.WHISPER_METHOD) if config.WHISPER_METHOD in whisper_method_options else 0)
    if selected_whisper_method != config.WHISPER_METHOD:
        changes["WHISPER_METHOD"] = selected_whisper_method
    # 如果是whisperxapi，则需要填写Replicate API Token
    if selected_whisper_method == "whisperxapi":    
        replicate_api_token = st.text_input("Replicate API Token:", value=config.REPLICATE_API_TOKEN, help="调用whisperX api用，获取地址：https://replicate.com/account/api-tokens")
        if replicate_api_token != config.REPLICATE_API_TOKEN:
            changes["REPLICATE_API_TOKEN"] = replicate_api_token
        
    lang_cols = st.columns(2)
    with lang_cols[0]:
        whisper_language_options = ["auto", "en"]
        selected_whisper_language = st.selectbox("Whisper识别语言:", options=whisper_language_options, index=whisper_language_options.index(config.WHISPER_LANGUAGE) if config.WHISPER_LANGUAGE in whisper_language_options else 0)
        if selected_whisper_language != config.WHISPER_LANGUAGE:
            changes["WHISPER_LANGUAGE"] = selected_whisper_language
    with lang_cols[1]:
        target_language = st.text_input("翻译目标语言:", value=config.TARGET_LANGUAGE)
        if target_language != config.TARGET_LANGUAGE:
            changes["TARGET_LANGUAGE"] = target_language

    st.write("每行字幕最大字符数：")
    max_length_cols = st.columns(2)
    with max_length_cols[0]:
        max_src_length = st.number_input("原字幕:", value=config.MAX_SRC_LENGTH)
        if max_src_length != config.MAX_SRC_LENGTH:
            changes["MAX_SRC_LENGTH"] = int(max_src_length)
    with max_length_cols[1]:
        max_target_language_length = st.number_input("翻译字幕:", value=config.MAX_TARGET_LANGUAGE_LENGTH)
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

    #! 配音功能仍在开发中，暂已停用，感谢理解！
    # st.header("SoVITS 角色配置")
    # dubbing_character = st.text_input("配音角色:", value=config.DUBBNING_CHARACTER)
    # if dubbing_character != config.DUBBNING_CHARACTER:
    #     changes["DUBBNING_CHARACTER"] = dubbing_character
    
    if changes:
        st.toast("记得点击下方的'保存设置'按钮", icon="🔔")
    
    st.markdown("")
    cols_save = st.columns(2)
    with cols_save[0]:
        if st.button("保    存", use_container_width = True):
            for key, value in changes.items():
                update_config(key, value)
            st.toast("设置已更新", icon="✅")
            changes.clear()  # 清空更改字典
    with cols_save[1]:
        if st.button("验    证",use_container_width = True):
            st.toast("正在尝试访问...", icon="🔄")
            try:
                response = ask_gpt("this is a test, response 'code':'200' in json format.", model=config.MODEL[0], response_json=True, log_title='None')
                if response.get('code') == '200':
                    st.toast("验证成功", icon="✅")
                else:
                    st.toast("验证失败, 请检查 API_KEY 和 BASE_URL 是否正确", icon="❌")
            except Exception as e:
                st.toast(f"访问失败 {e}", icon="❌")