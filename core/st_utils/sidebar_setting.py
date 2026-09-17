import hashlib

import requests
import streamlit as st

from translations.translations import translate as t
from core.tts_backend.voxcpm_tts import (
    MANUAL_REFERENCE_AUDIO_PATH,
    save_voxcpm_reference_audio,
)
from core.utils import *


_MISSING = object()


def _css_text(value):
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def _inject_voxcpm_styles():
    browse_text = _css_text(t("Upload attachment"))
    st.markdown(
        f"""
        <style>
        .st-key-voxcpm_voice_settings {{
            border-top: 1px solid color-mix(in srgb, var(--text-color) 14%, transparent);
            margin-top: 0.75rem;
            padding-top: 0.85rem;
        }}
        .st-key-voxcpm_mode_selector [data-testid="stSegmentedControl"] {{
            width: 100%;
        }}
        .st-key-voxcpm_mode_selector [data-testid="stSegmentedControl"] button {{
            min-height: 2.5rem;
            flex: 1 1 0;
        }}
        .st-key-voxcpm_mode_selector [role="radio"][aria-checked="true"] {{
            color: var(--text-color) !important;
            background: var(--background-color) !important;
            box-shadow: inset 0 -2px 0 var(--primary-color);
        }}
        .st-key-voxcpm_reference_upload {{
            margin-top: -0.3rem;
        }}
        .st-key-voxcpm_reference_upload [data-testid="stFileUploaderDropzone"] {{
            min-height: 0 !important;
            padding: 0 !important;
            border: 0 !important;
            border-radius: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
        }}
        .st-key-voxcpm_reference_upload div[data-testid="stFileUploaderDropzoneInstructions"] {{
            display: none !important;
        }}
        .st-key-voxcpm_reference_upload div[data-testid="stFileUploader"] button[kind="secondary"] {{
            width: 100%;
            min-height: 2.6rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.45rem;
            font-size: 0 !important;
        }}
        .st-key-voxcpm_reference_upload div[data-testid="stFileUploader"] button[kind="secondary"] > div {{
            display: none !important;
        }}
        .st-key-voxcpm_reference_upload div[data-testid="stFileUploader"] button[kind="secondary"]::before {{
            content: "{browse_text}";
            font-size: 0.875rem;
        }}
        .st-key-voxcpm_reference_upload div[data-testid="stFileUploader"] button[kind="secondary"]::after {{
            content: "upload";
            font-family: "Material Symbols Rounded";
            font-size: 1.05rem;
            font-weight: 400;
            line-height: 1;
        }}
        [class*="st-key-voxcpm_reference_transcript_"] {{
            margin-top: -0.35rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def config_input(label, key, help=None, placeholder=None, input_type="default", default=_MISSING):
    """Generic config input handler"""
    current = load_key(key) if default is _MISSING else load_key_or(key, default)
    val = st.text_input(
        label,
        value=current,
        help=help,
        placeholder=placeholder,
        type=input_type,
    )
    if val != current:
        if default is _MISSING:
            update_key(key, val)
        else:
            set_key(key, val)
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
        """
        <style>
        [data-testid="stSidebar"] {
            width: min(420px, 100vw) !important;
            min-width: min(420px, 100vw) !important;
            max-width: 420px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

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
                "Auto": "auto",
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

        runtimes = ["local", "elevenlabs"]
        configured_runtime = load_key("whisper.runtime")
        if configured_runtime not in runtimes:
            st.warning(t("The 302.ai WhisperX cloud service has been retired. Select Local or ElevenLabs to continue."))
        runtime = st.selectbox(
            t("WhisperX Runtime"),
            options=runtimes,
            index=runtimes.index(configured_runtime) if configured_runtime in runtimes else None,
            format_func=lambda x: {
                "local": t("Local"),
                "elevenlabs": t("ElevenLabs"),
            }[x],
            help=t(
                "Local runtime requires >8GB GPU; ElevenLabs runtime requires an ElevenLabs API key."
            ),
        )
        if runtime is not None and runtime != configured_runtime:
            update_key("whisper.runtime", runtime)
            st.rerun()
        if runtime == "elevenlabs":
            config_input(t("ElevenLabs API"), "whisper.elevenlabs_api_key")

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

        from core._1_ytdlp import is_audio_only_input
        audio_only = is_audio_only_input()
        if audio_only:
            st.toggle(
                t("Burn-in Subtitles"),
                value=False,
                disabled=True,
                help=t("Audio-only input produces subtitle files only; no video is generated."),
            )
        else:
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
            "voxcpm",
        ]
        tts_method_labels = {
            "azure_tts": t("Azure TTS"),
            "openai_tts": t("OpenAI TTS"),
            "fish_tts": t("Fish TTS"),
            "sf_fish_tts": t("SiliconFlow Fish TTS"),
            "edge_tts": t("Edge TTS"),
            "gpt_sovits": t("GPT-SoVITS"),
            "custom_tts": t("Custom TTS"),
            "sf_cosyvoice2": t("SiliconFlow CosyVoice2"),
            "f5tts": t("F5-TTS"),
            "voxcpm": t("ModelBest VoxCPM"),
        }
        select_tts = st.selectbox(
            t("TTS Method"),
            options=tts_methods,
            index=tts_methods.index(load_key("tts_method")),
            format_func=lambda x: tts_method_labels[x],
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
                config_input(t("Voice"), "sf_fish_tts.voice")

        elif select_tts == "openai_tts":
            config_input(t("302ai API"), "openai_tts.api_key")
            config_input(t("OpenAI Voice"), "openai_tts.voice")

        elif select_tts == "fish_tts":
            config_input(t("302ai API"), "fish_tts.api_key")
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
            config_input(t("302ai API"), "azure_tts.api_key")
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
            config_input(t("302ai API"), "f5tts.302_api")

        elif select_tts == "voxcpm":
            _inject_voxcpm_styles()

            with st.container(key="voxcpm_service_settings"):
                st.markdown(f"**{t('VoxCPM Service Settings')}**")
                config_input(
                    t("VoxCPM API Key"),
                    "voxcpm.api_key",
                    input_type="password",
                    default="",
                )
                config_input(
                    t("VoxCPM Model ID"),
                    "voxcpm.model_id",
                    default="VoxCPM2",
                )
                config_input(
                    t("VoxCPM Base URL"),
                    "voxcpm.base_url",
                    default="https://api.modelbest.cn/v1",
                )

            mode_options = ["default", "clone", "high_fidelity"]
            current_mode = load_key_or("voxcpm.mode", None)
            if current_mode not in mode_options:
                legacy_high_fidelity = load_key_or("voxcpm.high_fidelity", None)
                if legacy_high_fidelity is True:
                    current_mode = "high_fidelity"
                elif legacy_high_fidelity is False:
                    current_mode = "default"
                else:
                    current_mode = "clone"
            mode_labels = {
                "default": t("VoxCPM Default Voice"),
                "clone": t("VoxCPM Voice Clone"),
                "high_fidelity": t("VoxCPM High-fidelity Clone"),
            }
            mode_captions = {
                "default": t("VoxCPM Default Voice Caption"),
                "clone": t("VoxCPM Voice Clone Caption"),
                "high_fidelity": t("VoxCPM High-fidelity Clone Caption"),
            }
            with st.container(key="voxcpm_voice_settings"):
                st.markdown(f"**{t('VoxCPM Voice Settings')}**")
                selected_mode = st.segmented_control(
                    t("VoxCPM Mode"),
                    options=mode_options,
                    default=current_mode,
                    format_func=lambda mode: mode_labels[mode],
                    help=t("VoxCPM Mode Help"),
                    width="stretch",
                    key="voxcpm_mode_selector",
                    label_visibility="collapsed",
                )
                if selected_mode:
                    st.caption(mode_captions[selected_mode])
            if selected_mode and selected_mode != current_mode:
                set_key("voxcpm.mode", selected_mode)
                st.rerun()

            if selected_mode != "default":
                reference_path = MANUAL_REFERENCE_AUDIO_PATH
                previous_reference_id = (
                    hashlib.sha256(reference_path.read_bytes()).hexdigest()
                    if reference_path.exists()
                    else None
                )
                uploader_version = st.session_state.get(
                    "_voxcpm_reference_uploader_version", 0
                )
                prompt_version = st.session_state.get("_voxcpm_prompt_version", 0)
                with st.container(key="voxcpm_reference_upload"):
                    uploaded_reference = st.file_uploader(
                        t("VoxCPM Reference Audio"),
                        type=load_key("allowed_audio_formats"),
                        key=f"voxcpm_reference_audio_upload_{uploader_version}",
                        help=t("VoxCPM Reference Audio Help"),
                        max_upload_size=50,
                    )
                if uploaded_reference is not None:
                    uploaded_bytes = uploaded_reference.getvalue()
                    upload_id = hashlib.sha256(uploaded_bytes).hexdigest()
                    if st.session_state.get("_voxcpm_reference_upload_id") != upload_id:
                        try:
                            save_voxcpm_reference_audio(uploaded_bytes)
                        except ValueError as exc:
                            st.error(
                                t("VoxCPM Reference Audio Error").replace(
                                    "{error}", str(exc)
                                )
                            )
                        else:
                            saved_reference_id = hashlib.sha256(
                                reference_path.read_bytes()
                            ).hexdigest()
                            if saved_reference_id != previous_reference_id:
                                set_key("voxcpm.prompt_text", "")
                                prompt_version += 1
                                st.session_state["_voxcpm_prompt_version"] = prompt_version
                            st.session_state["_voxcpm_reference_upload_id"] = upload_id
                            st.success(t("VoxCPM Reference Audio Saved"))

                if reference_path.exists():
                    st.caption(t("VoxCPM Reference Audio Ready"))
                    st.audio(str(reference_path), format="audio/wav")
                    if st.button(
                        t("Clear VoxCPM Reference Audio"),
                        key="clear_voxcpm_reference_audio",
                        icon=":material/delete:",
                        width="stretch",
                    ):
                        reference_path.unlink(missing_ok=True)
                        set_key("voxcpm.prompt_text", "")
                        st.session_state.pop("_voxcpm_reference_upload_id", None)
                        st.session_state["_voxcpm_reference_uploader_version"] = (
                            uploader_version + 1
                        )
                        st.session_state["_voxcpm_prompt_version"] = prompt_version + 1
                        st.rerun()
                else:
                    st.caption(t("VoxCPM Automatic Reference Audio"))

                if selected_mode == "high_fidelity":
                    current_prompt_text = load_key_or("voxcpm.prompt_text", "") or ""
                    prompt_text = st.text_area(
                        t("VoxCPM Reference Transcript"),
                        value=current_prompt_text,
                        height=96,
                        placeholder=t("VoxCPM Reference Transcript Placeholder"),
                        help=t("VoxCPM Reference Transcript Help"),
                        key=f"voxcpm_reference_transcript_{prompt_version}",
                    )
                    if prompt_text != current_prompt_text:
                        set_key("voxcpm.prompt_text", prompt_text)
                    if reference_path.exists() and not prompt_text.strip():
                        st.warning(t("VoxCPM Reference Transcript Required"))


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
