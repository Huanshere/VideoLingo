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
    
    api_key = st.text_input("API_KEU", value=config.API_KEY)
    whisper_api_key = st.text_input("WHISPER_API_KEY(纯 AZ 渠道)", value=config.WHISPER_API_KEY)
    base_url = st.text_input("BASE_URL", value=config.BASE_URL)
    models = st.text_input("MODEL", value=','.join(config.MODEL))
    
    if api_key != config.API_KEY:
        changes["API_KEY"] = api_key
    if whisper_api_key != config.WHISPER_API_KEY:
        changes["WHISPER_API_KEY"] = whisper_api_key
    if base_url != config.BASE_URL:
        changes["BASE_URL"] = base_url
    if models.split(',') != config.MODEL:
        changes["MODEL"] = models.split(',')
    
    st.header("字幕设置")
    target_language = st.text_input("翻译目标语言:", value=config.TARGET_LANGUAGE)
    if target_language != config.TARGET_LANGUAGE:
        changes["TARGET_LANGUAGE"] = target_language
    st.write("每行字幕最大字符数：")
    cols_sub = st.columns(2)
    with cols_sub[0]:
        max_src_length = st.number_input("原字幕:", value=config.MAX_SRC_LENGTH)
        if max_src_length != config.MAX_SRC_LENGTH:
            changes["MAX_SRC_LENGTH"] = int(max_src_length)
    
    with cols_sub[1]:
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
                response = ask_gpt("this is a test, response 'code':'200' in json format.", model=config.MODEL[0], response_json=True)
                if response.get('code') == '200':
                    st.toast("验证成功", icon="✅")
                else:
                    st.toast("验证失败, 请检查 API_KEY 和 BASE_URL 是否正确", icon="❌")
            except Exception as e:
                st.toast(f"访问失败 {e}", icon="❌")