import streamlit as st
import requests
from translations.translations import translate as t
from translations.translations import DISPLAY_LANGUAGES
from core.utils import *


def config_input(label, key, help=None, placeholder=None):
    """Generic config input handler"""
    val = st.text_input(label, value=load_key(key), help=help, placeholder=placeholder)
    if val != load_key(key):
        update_key(key, val)
    return val


def _fetch_model_list(base_url, api_key):
    """Fetch available models from OpenAI-compatible /v1/models endpoint."""
    if not api_key or not base_url:
        return []
    url = base_url.rstrip("/")
    if not url.endswith("/v1"):
        url += "/v1"
    url += "/models"
    try:
        resp = requests.get(
            url, headers={"Authorization": f"Bearer {api_key}"}, timeout=10
        )
        resp.raise_for_status()
        data = resp.json().get("data", [])
        return sorted([m["id"] for m in data if "id" in m])
    except Exception:
        return []


def _search_models(search_term, **kwargs):
    """Search function for st_searchbox — returns models matching the search term."""
    models = st.session_state.get("_model_list", [])
    if not search_term:
        return models if models else []
    term = search_term.lower()
    matched = [m for m in models if term in m.lower()]
    # Always include the raw input as an option so users can type custom model names
    if search_term not in matched:
        matched.insert(0, search_term)
    return matched


def page_setting():
    # Widen the sidebar slightly to accommodate the model searchbox
    st.markdown(
        """<style>[data-testid="stSidebar"] {min-width: 420px; max-width: 420px;}</style>""",
        unsafe_allow_html=True,
    )

    display_language = st.selectbox(
        "Display Language 🌐",
        options=list(DISPLAY_LANGUAGES.keys()),
        index=list(DISPLAY_LANGUAGES.values()).index(load_key("display_language")),
    )
    if DISPLAY_LANGUAGES[display_language] != load_key("display_language"):
        update_key("display_language", DISPLAY_LANGUAGES[display_language])
        st.rerun()

    # with st.expander(t("Youtube Settings"), expanded=True):
    #     config_input(t("Cookies Path"), "youtube.cookies_path")

    with st.expander(t("LLM Configuration"), expanded=True):
        config_input(t("API_KEY"), "api.key", placeholder=t("Enter your API key"))
        config_input(
            t("BASE_URL"),
            "api.base_url",
            help=t("Openai format, will add /v1/chat/completions automatically"),
        )

        # Try to use searchbox for model selection, fall back to text_input
        try:
            from streamlit_searchbox import st_searchbox
            from streamlit_searchbox import _list_to_options_js, _list_to_options_py

            if st.button(
                t("Fetch Model List"), key="fetch_models", use_container_width=True
            ):
                with st.spinner(t("Fetching models...")):
                    models = _fetch_model_list(
                        load_key("api.base_url"), load_key("api.key")
                    )
                    st.session_state["_model_list"] = models
                    if models:
                        # Update searchbox internal state directly so dropdown shows options
                        sb_key = "model_searchbox"
                        if sb_key in st.session_state:
                            st.session_state[sb_key]["options_js"] = (
                                _list_to_options_js(models)
                            )
                            st.session_state[sb_key]["options_py"] = (
                                _list_to_options_py(models)
                            )
                        st.toast(
                            t("Fetched {n} models").replace("{n}", str(len(models))),
                            icon="✅",
                        )
                    else:
                        st.toast(
                            t(
                                "Failed to fetch models, please check API Key and Base URL"
                            ),
                            icon="❌",
                        )

            current_model = load_key("api.model")
            model_list = st.session_state.get("_model_list", None)

            sb_key = "model_searchbox"
            selected = st_searchbox(
                _search_models,
                placeholder=t("Search or enter model name"),
                default=current_model if current_model else None,
                default_searchterm=current_model if current_model else "",
                default_use_searchterm=True,
                default_options=model_list if model_list else None,
                key=sb_key,
                clear_on_submit=False,
            )
            if selected and selected != load_key("api.model"):
                update_key("api.model", selected)

            if st.button("📡 " + t("Check API"), key="api", use_container_width=True):
                with st.spinner(t("Check API") + "..."):
                    is_valid = check_api()
                st.toast(
                    t("API Key is valid") if is_valid else t("API Key is invalid"),
                    icon="✅" if is_valid else "❌",
                )
        except ImportError:
            c1, c2 = st.columns([4, 1])
            with c1:
                config_input(
                    t("MODEL"),
                    "api.model",
                    help=t("click to check API validity") + " 👉",
                    placeholder=t("Search or enter model name"),
                )
            with c2:
                if st.button("📡", key="api"):
                    is_valid = check_api()
                    st.toast(
                        t("API Key is valid") if is_valid else t("API Key is invalid"),
                        icon="✅" if is_valid else "❌",
                    )
        llm_support_json = st.toggle(
            t("LLM JSON Format Support"),
            value=load_key("api.llm_support_json"),
            help=t("Enable if your LLM supports JSON mode output"),
        )
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
                "🇯🇵 日本語": "ja",
            }
            lang = st.selectbox(
                t("Recog Lang"),
                options=list(langs.keys()),
                index=list(langs.values()).index(load_key("whisper.language")),
            )
            if langs[lang] != load_key("whisper.language"):
                update_key("whisper.language", langs[lang])
                st.rerun()

        runtime = st.selectbox(
            t("WhisperX Runtime"),
            options=["local", "cloud", "elevenlabs"],
            index=["local", "cloud", "elevenlabs"].index(load_key("whisper.runtime")),
            help=t(
                "Local runtime requires >8GB GPU, cloud runtime requires 302ai API key, elevenlabs runtime requires ElevenLabs API key"
            ),
        )
        if runtime != load_key("whisper.runtime"):
            update_key("whisper.runtime", runtime)
            st.rerun()
        if runtime == "cloud":
            config_input(t("WhisperX 302ai API"), "whisper.whisperX_302_api_key")
        if runtime == "elevenlabs":
            config_input(("ElevenLabs API"), "whisper.elevenlabs_api_key")

        with c2:
            target_language = st.text_input(
                t("Target Lang"),
                value=load_key("target_language"),
                help=t(
                    "Input any language in natural language, as long as llm can understand"
                ),
            )
            if target_language != load_key("target_language"):
                update_key("target_language", target_language)
                st.rerun()

        demucs = st.toggle(
            t("Vocal separation enhance"),
            value=load_key("demucs"),
            help=t(
                "Recommended for videos with loud background noise, but will increase processing time"
            ),
        )
        if demucs != load_key("demucs"):
            update_key("demucs", demucs)
            st.rerun()

        burn_subtitles = st.toggle(
            t("Burn-in Subtitles"),
            value=load_key("burn_subtitles"),
            help=t(
                "Whether to burn subtitles into the video, will increase processing time"
            ),
        )
        if burn_subtitles != load_key("burn_subtitles"):
            update_key("burn_subtitles", burn_subtitles)
            st.rerun()

        subtitle_format = st.selectbox(
            t("Subtitle Format"),
            options=['srt', 'ass'],
            index=['srt', 'ass'].index(load_key("subtitle.format") or 'srt'),
            help=t("ASS format supports more style customization"),
        )
        if subtitle_format != (load_key("subtitle.format") or 'srt'):
            update_key("subtitle.format", subtitle_format)
            st.rerun()

        if subtitle_format == 'srt':
            with st.expander(t("SRT Style Settings")):
                srt_style = load_key("subtitle.srt_style") or {}
                src_style = srt_style.get('source', {})
                trans_style = srt_style.get('translation', {})

                st.subheader(t("Source Subtitle Style"))
                src_fontname = st.text_input(t("Source Font Name"), value=src_style.get('fontname', 'Arial'))
                src_fontsize = st.number_input(t("Source Font Size"), value=int(src_style.get('fontsize', 15)), min_value=1)
                src_primary = st.text_input(t("Source Primary Color"), value=src_style.get('primary_color', '&HFFFFFF'))
                src_outline = st.text_input(t("Source Outline Color"), value=src_style.get('outline_color', '&H000000'))
                src_outline_w = st.number_input(t("Source Outline Width"), value=float(src_style.get('outline_width', 1.0)), min_value=0.0, step=0.5)
                src_shadow_color = st.text_input(t("Source Shadow Color"), value=src_style.get('shadow_color', '&H80000000'))
                src_border_opts = sorted(set([1, 3, 4] + [int(src_style.get('border_style', 1))]))
                src_border_default = int(src_style.get('border_style', 1))
                src_border = st.selectbox(t("Source Border Style"), options=src_border_opts, index=src_border_opts.index(src_border_default) if src_border_default in src_border_opts else 0)
                align_opts = sorted(set(list(range(1, 10)) + [int(src_style.get('alignment', 8))]))
                src_align_default = int(src_style.get('alignment', 8))
                src_align = st.selectbox(t("Source Alignment"), options=align_opts, index=align_opts.index(src_align_default) if src_align_default in align_opts else 7)
                src_marginv = st.number_input(t("Source Margin V"), value=int(src_style.get('margin_v', 10)), min_value=0)
                src_marginl = st.number_input(t("Source Margin L"), value=int(src_style.get('margin_l', 10)), min_value=0)
                src_marginr = st.number_input(t("Source Margin R"), value=int(src_style.get('margin_r', 10)), min_value=0)

                st.subheader(t("Translation Subtitle Style"))
                trans_fontname = st.text_input(t("Translation Font Name"), value=trans_style.get('fontname', 'Arial'))
                trans_fontsize = st.number_input(t("Translation Font Size"), value=int(trans_style.get('fontsize', 17)), min_value=1)
                trans_primary = st.text_input(t("Translation Primary Color"), value=trans_style.get('primary_color', '&H00FFFF'))
                trans_outline = st.text_input(t("Translation Outline Color"), value=trans_style.get('outline_color', '&H000000'))
                trans_outline_w = st.number_input(t("Translation Outline Width"), value=float(trans_style.get('outline_width', 1.0)), min_value=0.0, step=0.5)
                trans_back = st.text_input(t("Translation Back Color"), value=trans_style.get('back_color', '&H33000000'))
                trans_border_opts = sorted(set([1, 3, 4] + [int(trans_style.get('border_style', 4))]))
                trans_border_default = int(trans_style.get('border_style', 4))
                trans_border = st.selectbox(t("Translation Border Style"), options=trans_border_opts, index=trans_border_opts.index(trans_border_default) if trans_border_default in trans_border_opts else 0)
                trans_align_opts = sorted(set(list(range(1, 10)) + [int(trans_style.get('alignment', 2))]))
                trans_align_default = int(trans_style.get('alignment', 2))
                trans_align = st.selectbox(t("Translation Alignment"), options=trans_align_opts, index=trans_align_opts.index(trans_align_default) if trans_align_default in trans_align_opts else 1)
                trans_marginv = st.number_input(t("Translation Margin V"), value=int(trans_style.get('margin_v', 27)), min_value=0)
                trans_marginl = st.number_input(t("Translation Margin L"), value=int(trans_style.get('margin_l', 10)), min_value=0)
                trans_marginr = st.number_input(t("Translation Margin R"), value=int(trans_style.get('margin_r', 10)), min_value=0)

                if st.button(t("Save SRT Style")):
                    update_key("subtitle.srt_style.source", {
                        'fontname': src_fontname, 'fontsize': src_fontsize,
                        'primary_color': src_primary, 'outline_color': src_outline,
                        'outline_width': src_outline_w, 'shadow_color': src_shadow_color,
                        'border_style': src_border, 'alignment': src_align,
                        'margin_v': src_marginv, 'margin_l': src_marginl, 'margin_r': src_marginr,
                    })
                    update_key("subtitle.srt_style.translation", {
                        'fontname': trans_fontname, 'fontsize': trans_fontsize,
                        'primary_color': trans_primary, 'outline_color': trans_outline,
                        'outline_width': trans_outline_w, 'back_color': trans_back,
                        'border_style': trans_border, 'alignment': trans_align,
                        'margin_v': trans_marginv, 'margin_l': trans_marginl, 'margin_r': trans_marginr,
                    })
                    st.toast(t("SRT style saved"))
        elif subtitle_format == 'ass':
            with st.expander(t("ASS Style Settings")):
                ass_style = load_key("subtitle.ass_style") or {}

                # ---- Import ----
                with st.expander(t("Import ASS Style")):
                    pasted_style = st.text_area(
                        t("Paste ASS Style line"),
                        placeholder='Style: Default,微软雅黑,54,&H00FFFFFF,...',
                        height=80,
                    )
                    import_target = st.radio(
                        t("Apply to"),
                        options=['source', 'translation', 'both'],
                        format_func=lambda x: {
                            'source': t('Source'),
                            'translation': t('Translation'),
                            'both': t('Both'),
                        }[x],
                        horizontal=True,
                    )
                    if st.button(t("Import Style")):
                        from core.utils.ass_utils import parse_ass_style_line
                        try:
                            parsed = parse_ass_style_line(pasted_style)
                            if import_target in ('source', 'both'):
                                update_key("subtitle.ass_style.source", parsed)
                            if import_target in ('translation', 'both'):
                                update_key("subtitle.ass_style.translation", parsed)
                            st.toast(t("Style imported successfully"))
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))

                scale_mode = st.radio(
                    t("Font Size Mode"),
                    options=['absolute', 'relative'],
                    format_func=lambda x: t("Absolute Pixels") if x == 'absolute' else t("Relative Scaling"),
                    index=['absolute', 'relative'].index(ass_style.get('scale_mode', 'absolute')),
                    help=t("Absolute: fontsize = pixels, same as SRT. Relative: fontsize scales with video resolution"),
                )
                if scale_mode != ass_style.get('scale_mode', 'absolute'):
                    update_key("subtitle.ass_style.scale_mode", scale_mode)
                    st.rerun()

                if scale_mode == 'relative':
                    prx = st.number_input("PlayResX", value=int(ass_style.get('play_res_x', 1920)))
                    pry = st.number_input("PlayResY", value=int(ass_style.get('play_res_y', 1080)))
                    if prx != ass_style.get('play_res_x', 1920):
                        update_key("subtitle.ass_style.play_res_x", prx)
                    if pry != ass_style.get('play_res_y', 1080):
                        update_key("subtitle.ass_style.play_res_y", pry)

                src_style = ass_style.get('source', {})
                trans_style = ass_style.get('translation', {})

                st.subheader(t("Source Subtitle Style"))
                src_fontname = st.text_input(t("Source Font Name"), value=src_style.get('fontname', 'Arial'))
                src_fontsize = st.number_input(t("Source Font Size"), value=int(src_style.get('fontsize', 17)), min_value=1)
                src_primary = st.text_input(t("Source Primary Color"), value=src_style.get('primary_color', '&HFFFFFF'))
                src_secondary = st.text_input(t("Source Secondary Color"), value=src_style.get('secondary_color', '&HFFFFFF'))
                src_outline = st.text_input(t("Source Outline Color"), value=src_style.get('outline_color', '&H000000'))
                src_outline_w = st.number_input(t("Source Outline Width"), value=float(src_style.get('outline_width', 1.0)), min_value=0.0, step=0.5)
                src_shadow_depth = st.number_input(t("Source Shadow Depth"), value=float(src_style.get('shadow', 0.0)), min_value=0.0, step=0.5)
                src_border_opts = sorted(set([1, 3, 4] + [int(src_style.get('border_style', 1))]))
                src_border_default = int(src_style.get('border_style', 1))
                src_border = st.selectbox(t("Source Border Style"), options=src_border_opts, index=src_border_opts.index(src_border_default) if src_border_default in src_border_opts else 0)
                align_opts = sorted(set(list(range(1, 10)) + [int(src_style.get('alignment', 8))]))
                src_align_default = int(src_style.get('alignment', 8))
                src_align = st.selectbox(t("Source Alignment"), options=align_opts, index=align_opts.index(src_align_default) if src_align_default in align_opts else 7)
                src_marginv = st.number_input(t("Source Margin V"), value=int(src_style.get('margin_v', 10)), min_value=0)

                st.subheader(t("Translation Subtitle Style"))
                trans_fontname = st.text_input(t("Translation Font Name"), value=trans_style.get('fontname', 'Arial'))
                trans_fontsize = st.number_input(t("Translation Font Size"), value=int(trans_style.get('fontsize', 17)), min_value=1)
                trans_primary = st.text_input(t("Translation Primary Color"), value=trans_style.get('primary_color', '&H00FFFF'))
                trans_secondary = st.text_input(t("Translation Secondary Color"), value=trans_style.get('secondary_color', '&H00FFFF'))
                trans_outline = st.text_input(t("Translation Outline Color"), value=trans_style.get('outline_color', '&H000000'))
                trans_outline_w = st.number_input(t("Translation Outline Width"), value=float(trans_style.get('outline_width', 1.0)), min_value=0.0, step=0.5)
                trans_shadow_depth = st.number_input(t("Translation Shadow Depth"), value=float(trans_style.get('shadow', 0.0)), min_value=0.0, step=0.5)
                trans_back = st.text_input(t("Translation Back Color"), value=trans_style.get('back_color', '&H33000000'))
                trans_border_opts = sorted(set([1, 3, 4] + [int(trans_style.get('border_style', 4))]))
                trans_border_default = int(trans_style.get('border_style', 4))
                trans_border = st.selectbox(t("Translation Border Style"), options=trans_border_opts, index=trans_border_opts.index(trans_border_default) if trans_border_default in trans_border_opts else 0)
                trans_align_opts = sorted(set(list(range(1, 10)) + [int(trans_style.get('alignment', 2))]))
                trans_align_default = int(trans_style.get('alignment', 2))
                trans_align = st.selectbox(t("Translation Alignment"), options=trans_align_opts, index=trans_align_opts.index(trans_align_default) if trans_align_default in trans_align_opts else 1)
                trans_marginv = st.number_input(t("Translation Margin V"), value=int(trans_style.get('margin_v', 27)), min_value=0)

                if st.button(t("Save ASS Style")):
                    update_key("subtitle.ass_style.source", {
                        'fontname': src_fontname, 'fontsize': src_fontsize,
                        'primary_color': src_primary, 'secondary_color': src_secondary,
                        'outline_color': src_outline, 'back_color': '&H000000',
                        'bold': 0, 'italic': 0,
                        'outline_width': src_outline_w, 'shadow': src_shadow_depth,
                        'shadow_color': '&H80000000',
                        'border_style': src_border, 'alignment': src_align,
                        'margin_l': 10, 'margin_r': 10, 'margin_v': src_marginv,
                    })
                    update_key("subtitle.ass_style.translation", {
                        'fontname': trans_fontname, 'fontsize': trans_fontsize,
                        'primary_color': trans_primary, 'secondary_color': trans_secondary,
                        'outline_color': trans_outline, 'back_color': trans_back,
                        'bold': 0, 'italic': 0,
                        'outline_width': trans_outline_w, 'shadow': trans_shadow_depth,
                        'border_style': trans_border, 'alignment': trans_align,
                        'margin_l': 10, 'margin_r': 10, 'margin_v': trans_marginv,
                    })
                    st.toast(t("ASS style saved"))
    with st.expander(t("Dubbing Settings"), expanded=True):
        tts_methods = [
            "azure_tts",
            "openai_tts",
            "fish_tts",
            "sf_fish_tts",
            "edge_tts",
            "gpt_sovits",
            "custom_tts",
            "sf_cosyvoice2",
            "f5tts",
        ]
        select_tts = st.selectbox(
            t("TTS Method"),
            options=tts_methods,
            index=tts_methods.index(load_key("tts_method")),
        )
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
                "dynamic": t("Refer_dynamic"),
            }
            selected_mode = st.selectbox(
                t("Mode Selection"),
                options=list(mode_options.keys()),
                format_func=lambda x: mode_options[x],
                index=list(mode_options.keys()).index(load_key("sf_fish_tts.mode"))
                if load_key("sf_fish_tts.mode") in mode_options.keys()
                else 0,
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
            fish_tts_character = st.selectbox(
                t("Fish TTS Character"),
                options=list(load_key("fish_tts.character_id_dict").keys()),
                index=list(load_key("fish_tts.character_id_dict").keys()).index(
                    load_key("fish_tts.character")
                ),
            )
            if fish_tts_character != load_key("fish_tts.character"):
                update_key("fish_tts.character", fish_tts_character)
                st.rerun()

        elif select_tts == "azure_tts":
            config_input("302ai API", "azure_tts.api_key")
            config_input(t("Azure Voice"), "azure_tts.voice")

        elif select_tts == "gpt_sovits":
            st.info(t("Please refer to Github homepage for GPT_SoVITS configuration"))
            config_input(t("SoVITS Character"), "gpt_sovits.character")

            refer_mode_options = {
                1: t("Mode 1: Use provided reference audio only"),
                2: t("Mode 2: Use first audio from video as reference"),
                3: t("Mode 3: Use each audio from video as reference"),
            }
            selected_refer_mode = st.selectbox(
                t("Refer Mode"),
                options=list(refer_mode_options.keys()),
                format_func=lambda x: refer_mode_options[x],
                index=list(refer_mode_options.keys()).index(
                    load_key("gpt_sovits.refer_mode")
                ),
                help=t("Configure reference audio mode for GPT-SoVITS"),
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


def check_api():
    try:
        resp = ask_gpt(
            "This is a test, response 'message':'success' in json format.",
            resp_type="json",
            log_title="None",
        )
        return resp.get("message") == "success"
    except Exception:
        return False


if __name__ == "__main__":
    check_api()
