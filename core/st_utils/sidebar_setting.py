import streamlit as st
from translations.translations import translate as t
from translations.translations import DISPLAY_LANGUAGES
from core.utils import *
import requests

def config_input(label, key, help=None):
    """Generic config input handler"""
    val = st.text_input(label, value=load_key(key), help=help)
    if val != load_key(key):
        update_key(key, val)
    return val

def page_setting():

    display_language = st.selectbox("Display Language 🌐", 
                                  options=list(DISPLAY_LANGUAGES.keys()),
                                  index=list(DISPLAY_LANGUAGES.values()).index(load_key("display_language")))
    if DISPLAY_LANGUAGES[display_language] != load_key("display_language"):
        update_key("display_language", DISPLAY_LANGUAGES[display_language])
        st.rerun()

    # with st.expander(t("Youtube Settings"), expanded=True):
    #     config_input(t("Cookies Path"), "youtube.cookies_path")

    with st.expander(t("LLM Configuration"), expanded=True):
        config_input(t("API_KEY"), "api.key")
        config_input(t("BASE_URL"), "api.base_url", help=t("Openai format, will add /v1/chat/completions automatically"))
        
        c1, c2 = st.columns([4, 1])
        with c1:
            config_input(t("MODEL"), "api.model", help=t("click to check API validity")+ " 👉")
        with c2:
            if st.button("📡", key="api"):
                st.toast(t("API Key is valid") if check_api() else t("API Key is invalid"), 
                        icon="✅" if check_api() else "❌")
        llm_support_json = st.toggle(t("LLM JSON Format Support"), value=load_key("api.llm_support_json"), help=t("Enable if your LLM supports JSON mode output"))
        if llm_support_json != load_key("api.llm_support_json"):
            update_key("api.llm_support_json", llm_support_json)
            st.rerun()
    with st.expander(t("Subtitles Settings"), expanded=True):
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
                t("Recog Lang"),
                options=list(langs.keys()),
                index=list(langs.values()).index(load_key("whisper.language"))
            )
            if langs[lang] != load_key("whisper.language"):
                update_key("whisper.language", langs[lang])
                st.rerun()

        runtime = st.selectbox(t("WhisperX Runtime"), options=["local", "cloud", "elevenlabs"], index=["local", "cloud", "elevenlabs"].index(load_key("whisper.runtime")), help=t("Local runtime requires >8GB GPU, cloud runtime requires 302ai API key, elevenlabs runtime requires ElevenLabs API key"))
        if runtime != load_key("whisper.runtime"):
            update_key("whisper.runtime", runtime)
            st.rerun()
        if runtime == "cloud":
            config_input(t("WhisperX 302ai API"), "whisper.whisperX_302_api_key")
        if runtime == "elevenlabs":
            config_input(("ElevenLabs API"), "whisper.elevenlabs_api_key")

        with c2:
            target_language = st.text_input(t("Target Lang"), value=load_key("target_language"), help=t("Input any language in natural language, as long as llm can understand"))
            if target_language != load_key("target_language"):
                update_key("target_language", target_language)
                st.rerun()

        demucs = st.toggle(t("Vocal separation enhance"), value=load_key("demucs"), help=t("Recommended for videos with loud background noise, but will increase processing time"))
        if demucs != load_key("demucs"):
            update_key("demucs", demucs)
            st.rerun()
        
        burn_subtitles = st.toggle(t("Burn-in Subtitles"), value=load_key("burn_subtitles"), help=t("Whether to burn subtitles into the video, will increase processing time"))
        if burn_subtitles != load_key("burn_subtitles"):
            update_key("burn_subtitles", burn_subtitles)
            st.rerun()
    with st.expander(t("Dubbing Settings"), expanded=True):
        tts_methods = ["azure_tts", "openai_tts", "fish_tts", "sf_fish_tts", "edge_tts", "gpt_sovits", "custom_tts", "sf_cosyvoice2", "f5tts"]
        select_tts = st.selectbox(t("TTS Method"), options=tts_methods, index=tts_methods.index(load_key("tts_method")))
        if select_tts != load_key("tts_method"):
            update_key("tts_method", select_tts)
            st.rerun()

        # sub settings for each tts method
        if select_tts == "sf_fish_tts":
            config_input(t("SiliconFlow API Key"), "sf_fish_tts.api_key")
            
            # Add mode selection dropdown
            mode_options = {
                "preset": t("Preset"),
                "custom": t("Refer_stable"),
                "dynamic": t("Refer_dynamic")
            }
            selected_mode = st.selectbox(
                t("Mode Selection"),
                options=list(mode_options.keys()),
                format_func=lambda x: mode_options[x],
                index=list(mode_options.keys()).index(load_key("sf_fish_tts.mode")) if load_key("sf_fish_tts.mode") in mode_options.keys() else 0
            )
            if selected_mode != load_key("sf_fish_tts.mode"):
                update_key("sf_fish_tts.mode", selected_mode)
                st.rerun()
            if selected_mode == "preset":
                config_input("Voice", "sf_fish_tts.voice")

        elif select_tts == "openai_tts":
            config_input("302ai API", "openai_tts.api_key")
            config_input(t("OpenAI Voice"), "openai_tts.voice")

        elif select_tts == "fish_tts":
            config_input("302ai API", "fish_tts.api_key")
            fish_tts_character = st.selectbox(t("Fish TTS Character"), options=list(load_key("fish_tts.character_id_dict").keys()), index=list(load_key("fish_tts.character_id_dict").keys()).index(load_key("fish_tts.character")))
            if fish_tts_character != load_key("fish_tts.character"):
                update_key("fish_tts.character", fish_tts_character)
                st.rerun()

        elif select_tts == "azure_tts":
            config_input("302ai API", "azure_tts.api_key")
            config_input(t("Azure Voice"), "azure_tts.voice")
        
        elif select_tts == "gpt_sovits":
            st.info(t("Please refer to Github homepage for GPT_SoVITS configuration"))
            config_input(t("SoVITS Character"), "gpt_sovits.character")
            
            refer_mode_options = {1: t("Mode 1: Use provided reference audio only"), 2: t("Mode 2: Use first audio from video as reference"), 3: t("Mode 3: Use each audio from video as reference")}
            selected_refer_mode = st.selectbox(
                t("Refer Mode"),
                options=list(refer_mode_options.keys()),
                format_func=lambda x: refer_mode_options[x],
                index=list(refer_mode_options.keys()).index(load_key("gpt_sovits.refer_mode")),
                help=t("Configure reference audio mode for GPT-SoVITS")
            )
            if selected_refer_mode != load_key("gpt_sovits.refer_mode"):
                update_key("gpt_sovits.refer_mode", selected_refer_mode)
                st.rerun()
                
        elif select_tts == "edge_tts":
            config_input(t("Edge TTS Voice"), "edge_tts.voice")

        elif select_tts == "sf_cosyvoice2":
            config_input(t("SiliconFlow API Key"), "sf_cosyvoice2.api_key")
        
        elif select_tts == "f5tts":
            config_input("302ai API", "f5tts.302_api")
            
    with st.expander(t("CapCut Settings"), expanded=True):
        # 显示CapCutAPI信息
        st.markdown(
            t("This feature is powered by [CapCutAPI](https://github.com/sun-guannan/CapCutAPI?tab=readme-ov-file), an open-source API for automating CapCut draft creation and editing."),
            unsafe_allow_html=True
        )
        
        # 添加额外的空间
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
        
        # 检查是否已安装CapCutAPI
        is_installed = load_key("capcut.installed") if "installed" in load_key("capcut") else False
        
        if not is_installed:
            # 显示安装按钮
            st.info(t("CapCutAPI is not installed. Install it to export translated videos to CapCut."))
            
            # 询问使用剪映还是剪映国际版
            editor_options = ["CapCut", "剪映"]
            editor_choice = st.radio(t("Which editor do you use?"), options=editor_options, index=0)
            
            if st.button(t("Install CapCutAPI"), type="primary"):
                # 创建一个容器来显示安装日志
                log_container = st.empty()
                log_container.info(t("Installing CapCutAPI..."))
                
                try:
                    # 检查目录是否存在，如果存在则先删除
                    import shutil, subprocess, sys, json, os
                    if os.path.exists("core/capcut_api"):
                        shutil.rmtree("core/capcut_api")
                        log_container.info(t("Removed existing CapCutAPI directory."))
                    
                    # 克隆CapCutAPI仓库
                    log_container.info(t("Cloning CapCutAPI repository..."))
                    subprocess.check_call(["git", "clone", "--depth=1", "https://github.com/sun-guannan/CapCutAPI.git", "core/capcut_api"])

                    
                    # 安装依赖
                    log_container.info(t("Installing dependencies..."))
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "core/capcut_api/requirements.txt"])
                    
                    # 复制配置文件
                    if not os.path.exists("core/capcut_api/config.json"):
                        shutil.copy("core/capcut_api/config.json.example", "core/capcut_api/config.json")
                        log_container.info(t("Created configuration file."))
                    
                    # 根据选择修改配置文件
                    with open("core/capcut_api/config.json", "r", encoding="utf-8") as f:
                        config = json.load(f)
                    
                    # 设置是否为国际版
                    config["is_capcut_env"] = editor_choice == "CapCut"
                    
                    # 保存修改后的配置
                    with open("core/capcut_api/config.json", "w", encoding="utf-8") as f:
                        json.dump(config, f, indent=2, ensure_ascii=False)
                    
                    # 更新VideoLingo配置
                    # update_key("capcut.editor", editor_choice)
                    update_key("capcut.installed", True)
                    
                    # 提示用户安装成功
                    log_container.success(t("✅ CapCutAPI installed successfully!"))
                    st.info(t("Note: CapCutAPI will use port 9001 by default. If you need to change the port, please edit core/capcut_api/config.json"))
                    
                    # 重新加载页面以显示剪映设置
                    st.rerun()
                    
                except Exception as e:
                    log_container.error(f"Installation failed: {str(e)}")
                    st.error(t("Failed to install CapCutAPI. Please try again or install manually."))
        else:
            # 已安装，显示正常的剪映设置
            from core.capcut_process.request_capcut_api import get_font_types
            from core.capcut_process.capcut_server_manager import start_capcut_server, stop_capcut_server, cleanup_capcut_server
            # 1. 剪映草稿目录设置
            draft_folder = st.text_input(
                t("CapCut Draft Folder"),
                value=load_key("capcut.draft_folder") if "draft_folder" in load_key("capcut") else "",
                help=t("The directory path where CapCut drafts are saved, get it from Global Settings->Draft Location, e.g.: C:\\Users\\Administrator\\AppData\\Local\\JianyingPro\\User Data\\Projects\\com.lveditor.draft"),
                placeholder=t("Please enter CapCut draft directory path")
            )
            if draft_folder != load_key("capcut.draft_folder") if "draft_folder" in load_key("capcut") else "":
                update_key("capcut.draft_folder", draft_folder)
            
            # 添加是否启用导出剪映功能的开关
            enable_capcut = st.toggle(
                t("Enable CapCut Export"),
                value=load_key("capcut.enable_export"),
                disabled=not draft_folder,  # 当剪映草稿目录为空时禁用
                help=t("When enabled, CapCut drafts will be automatically generated")
            )
            
            # 更新配置并启动/停止服务器
            if enable_capcut != load_key("capcut.enable_export"):
                update_key("capcut.enable_export", enable_capcut)
                st.rerun()
            
            # 根据开关状态启动或停止服务器
            if enable_capcut:
                pass
                start_capcut_server()
            else:
                stop_capcut_server()
                
            # 定义字体选项（所有tab共用）
            font_options = []
            if enable_capcut:
                try:
                    # 使用函数获取字体列表
                    data = get_font_types()
                    if data["success"] and data["output"]:
                        font_options = [item["name"] for item in data["output"]]
                    else:
                        # 如果API返回成功但没有数据，使用默认字体列表
                        font_options = []
                except Exception as e:
                    # 如果发生异常，延迟3秒后重试
                    try:
                        # 延迟3秒
                        import time
                        time.sleep(3)
                        # 重新尝试获取字体列表
                        data = get_font_types()
                        if data["success"] and data["output"]:
                            font_options = [item["name"] for item in data["output"]]
                        else:
                            font_options = []
                    except Exception as e2:
                        st.warning(t("Failed to get font types, try refreshing this page."))
                        font_options = []

            # 只有当启用导出剪映功能时，才显示文字字体设置
            if enable_capcut:
                # 2. 原始文本字体设置
                # 文本设置部分 - 使用tabs横向排布三种文本设置
                st.subheader(t("Text Settings"))
                
                # 创建三个横向排布的tab
                orig_tab, trans_tab, dub_tab = st.tabs([t("Original Text"), t("Translated Text"), t("Dubbed Text")])
            
                # 1. 原始文本设置
                with orig_tab:
                    # 原始文本字体
                    selected_orig_font = st.selectbox(
                        t("Font"),
                        options=font_options,
                        index=font_options.index(load_key("capcut.orig_text.font")) if load_key("capcut.orig_text.font") in font_options else 0,
                        key="orig_font"
                    )
                    if selected_orig_font != load_key("capcut.orig_text.font"):
                        update_key("capcut.orig_text.font", selected_orig_font)
                        st.rerun()
                    
                    # 原始文本字体大小
                    orig_font_size = st.slider(
                        t("Font Size"),
                        min_value=1,
                        max_value=100,
                        value=int(load_key("capcut.orig_text.font_size")) if load_key("capcut.orig_text.font_size") else 36,
                        key="orig_font_size"
                    )
                    if orig_font_size != load_key("capcut.orig_text.font_size"):
                        update_key("capcut.orig_text.font_size", orig_font_size)
                        st.rerun()
                    
                    # 原始文本字体颜色
                    orig_font_color = st.color_picker(
                        t("Font Color"),
                        value=load_key("capcut.orig_text.color") if load_key("capcut.orig_text.color") else "#FFCC00",
                        key="orig_font_color"
                    )
                    if orig_font_color != load_key("capcut.orig_text.color"):
                        update_key("capcut.orig_text.color", orig_font_color)
                        st.rerun()
                    
                    # Y方向位置移动（原始文本独立控制）
                    orig_y_offset = st.slider(
                        t("Vertical Position Offset"),
                        min_value=-2.0,
                        max_value=2.0,
                        value=float(load_key("capcut.orig_text.y_offset")) if load_key("capcut.orig_text.y_offset") is not None else 0.0,
                        step=0.1,
                        key="orig_y_offset",
                        help=t("Positive values move upward, 1 represents one video height")
                    )
                    if orig_y_offset != load_key("capcut.orig_text.y_offset"):
                        update_key("capcut.orig_text.y_offset", orig_y_offset)
                        st.rerun()
                    
                    # 描边设置
                    orig_stroke = st.toggle(
                        t("Stroke"),
                        value=load_key("capcut.orig_text.stroke") if load_key("capcut.orig_text.stroke") is not None else True,
                        key="orig_stroke"
                    )
                    if orig_stroke != load_key("capcut.orig_text.stroke"):
                        update_key("capcut.orig_text.stroke", orig_stroke)
                        st.rerun()
                    
                    if orig_stroke:
                        # 原始文本描边颜色
                        orig_stroke_color = st.color_picker(
                            t("Stroke Color"),
                            value=load_key("capcut.orig_text.stroke_color") if load_key("capcut.orig_text.stroke_color") else "#000000",
                            key="orig_stroke_color"
                        )
                        if orig_stroke_color != load_key("capcut.orig_text.stroke_color"):
                            update_key("capcut.orig_text.stroke_color", orig_stroke_color)
                            st.rerun()
                            
                        # 原始文本描边粗细
                        orig_stroke_width = st.slider(
                            t("Stroke Width"),
                            min_value=0,
                            max_value=100,
                            value=int(load_key("capcut.orig_text.stroke_width")) if load_key("capcut.orig_text.stroke_width") else 30,
                            key="orig_stroke_width"
                        )
                        if orig_stroke_width != load_key("capcut.orig_text.stroke_width"):
                            update_key("capcut.orig_text.stroke_width", orig_stroke_width)
                            st.rerun()
                
                # 2. 翻译文本设置
                with trans_tab:
                    # 翻译文本字体
                    selected_trans_font = st.selectbox(
                        t("Font"),
                        options=font_options,
                        index=font_options.index(load_key("capcut.trans_text.font")) if load_key("capcut.trans_text.font") in font_options else 0,
                        key="trans_font"
                    )
                    if selected_trans_font != load_key("capcut.trans_text.font"):
                        update_key("capcut.trans_text.font", selected_trans_font)
                        st.rerun()
                    
                    # 翻译文本字体大小
                    trans_font_size = st.slider(
                        t("Font Size"),
                        min_value=1,
                        max_value=100,
                        value=int(load_key("capcut.trans_text.font_size")) if load_key("capcut.trans_text.font_size") else 36,
                        key="trans_font_size"
                    )
                    if trans_font_size != load_key("capcut.trans_text.font_size"):
                        update_key("capcut.trans_text.font_size", trans_font_size)
                        st.rerun()
                    
                    # 翻译文本字体颜色
                    trans_font_color = st.color_picker(
                        t("Font Color"),
                        value=load_key("capcut.trans_text.color") if load_key("capcut.trans_text.color") else "#FFFFFF",
                        key="trans_font_color"
                    )
                    if trans_font_color != load_key("capcut.trans_text.color"):
                        update_key("capcut.trans_text.color", trans_font_color)
                        st.rerun()
                    
                    # Y方向位置移动（翻译文本独立控制）
                    trans_y_offset = st.slider(
                        t("Vertical Position Offset"),
                        min_value=-2.0,
                        max_value=2.0,
                        value=float(load_key("capcut.trans_text.y_offset")) if load_key("capcut.trans_text.y_offset") is not None else 0.0,
                        step=0.1,
                        key="trans_y_offset",
                        help=t("Positive values move upward, 1 represents one video height")
                    )
                    if trans_y_offset != load_key("capcut.trans_text.y_offset"):
                        update_key("capcut.trans_text.y_offset", trans_y_offset)
                        st.rerun()
                    
                    # 描边设置
                    trans_stroke = st.toggle(
                        t("Stroke"),
                        value=load_key("capcut.trans_text.stroke") if load_key("capcut.trans_text.stroke") is not None else True,
                        key="trans_stroke"
                    )
                    if trans_stroke != load_key("capcut.trans_text.stroke"):
                        update_key("capcut.trans_text.stroke", trans_stroke)
                        st.rerun()
                    
                    if trans_stroke:
                        # 翻译文本描边颜色
                        trans_stroke_color = st.color_picker(
                            t("Stroke Color"),
                            value=load_key("capcut.trans_text.stroke_color") if load_key("capcut.trans_text.stroke_color") else "#000000",
                            key="trans_stroke_color"
                        )
                        if trans_stroke_color != load_key("capcut.trans_text.stroke_color"):
                            update_key("capcut.trans_text.stroke_color", trans_stroke_color)
                            st.rerun()
                            
                        # 翻译文本描边粗细
                        trans_stroke_width = st.slider(
                            t("Stroke Width"),
                            min_value=0,
                            max_value=100,
                            value=int(load_key("capcut.trans_text.stroke_width")) if load_key("capcut.trans_text.stroke_width") else 30,
                            key="trans_stroke_width"
                        )
                        if trans_stroke_width != load_key("capcut.trans_text.stroke_width"):
                            update_key("capcut.trans_text.stroke_width", trans_stroke_width)
                            st.rerun()
                
                # 3. 配音文本设置
                with dub_tab:
                    # 配音文本字体
                    selected_dub_font = st.selectbox(
                        t("Font"),
                        options=font_options,
                        index=font_options.index(load_key("capcut.dub_text.font")) if load_key("capcut.dub_text.font") in font_options else 0,
                        key="dub_font"
                    )
                    if selected_dub_font != load_key("capcut.dub_text.font"):
                        update_key("capcut.dub_text.font", selected_dub_font)
                        st.rerun()
                    
                    # 配音文本字体大小
                    dub_font_size = st.slider(
                        t("Font Size"),
                        min_value=1,
                        max_value=100,
                        value=int(load_key("capcut.dub_text.font_size")) if load_key("capcut.dub_text.font_size") else 8,
                        key="dub_font_size"
                    )
                    if dub_font_size != load_key("capcut.dub_text.font_size"):
                        update_key("capcut.dub_text.font_size", dub_font_size)
                        st.rerun()
                    
                    # 配音文本字体颜色
                    dub_font_color = st.color_picker(
                        t("Font Color"),
                        value=load_key("capcut.dub_text.color") if load_key("capcut.dub_text.color") else "#FFFFFF",
                        key="dub_font_color"
                    )
                    if dub_font_color != load_key("capcut.dub_text.color"):
                        update_key("capcut.dub_text.color", dub_font_color)
                        st.rerun()
                    
                    # Y方向位置移动（配音文本独立控制）
                    dub_y_offset = st.slider(
                        t("Vertical Position Offset"),
                        min_value=-3.0,
                        max_value=3.0,
                        value=float(load_key("capcut.dub_text.y_offset")) if load_key("capcut.dub_text.y_offset") is not None else 0.0,
                        step=0.1,
                        key="dub_y_offset",
                        help=t("Positive values move upward, 1 represents one video height")
                    )
                    if dub_y_offset != load_key("capcut.dub_text.y_offset"):
                        update_key("capcut.dub_text.y_offset", dub_y_offset)
                        st.rerun()
                    
                    # 描边设置
                    dub_stroke = st.toggle(
                        t("Stroke"),
                        value=load_key("capcut.dub_text.stroke") if load_key("capcut.dub_text.stroke") is not None else True,
                        key="dub_stroke"
                    )
                    if dub_stroke != load_key("capcut.dub_text.stroke"):
                        update_key("capcut.dub_text.stroke", dub_stroke)
                        st.rerun()
                    
                    if dub_stroke:
                        # 配音文本描边颜色
                        dub_stroke_color = st.color_picker(
                            t("Stroke Color"),
                            value=load_key("capcut.dub_text.stroke_color") if load_key("capcut.dub_text.stroke_color") else "#000000",
                            key="dub_stroke_color"
                        )
                        if dub_stroke_color != load_key("capcut.dub_text.stroke_color"):
                            update_key("capcut.dub_text.stroke_color", dub_stroke_color)
                            st.rerun()
                            
                        # 配音文本描边粗细
                        dub_stroke_width = st.slider(
                            t("Stroke Width"),
                            min_value=0,
                            max_value=100,
                            value=int(load_key("capcut.dub_text.stroke_width")) if load_key("capcut.dub_text.stroke_width") else 40,
                            key="dub_stroke_width"
                        )
                        if dub_stroke_width != load_key("capcut.dub_text.stroke_width"):
                            update_key("capcut.dub_text.stroke_width", dub_stroke_width)
                            st.rerun()
            
def check_api():
    try:
        resp = ask_gpt("This is a test, response 'message':'success' in json format.", 
                      resp_type="json", log_title='None')
        return resp.get('message') == 'success'
    except Exception:
        return False
    
if __name__ == "__main__":
    check_api()
