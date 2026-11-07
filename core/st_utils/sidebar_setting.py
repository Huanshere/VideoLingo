import hashlib
import importlib.util
import time

import requests
import streamlit as st

from translations.translations import translate as t
from core.tts_backend.voxcpm_tts import (
    MANUAL_REFERENCE_AUDIO_PATH,
    save_voxcpm_reference_audio,
)
from core.utils import *
from core.utils.ask_gpt import is_local_endpoint, normalize_base_url


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


def burned_subtitles_settings():
    """Which subtitles are burned into the subtitle video and into the dubbed video."""
    from core.utils.subtitle_style import BURN_MODES, BURN_MODE_KEYS, get_burn_mode
    labels = {"bilingual": t("Bilingual"), "translation": t("Translation only"), "source": t("Source only")}
    columns = st.columns(2)
    for column, video, label in zip(columns, ("subtitle", "dubbed"), (t("Subtitle video"), t("Dubbed video"))):
        key = BURN_MODE_KEYS[video][0]
        mode = get_burn_mode(video)
        with column:
            selected = st.selectbox(
                label,
                options=list(BURN_MODES),
                index=BURN_MODES.index(mode),
                format_func=labels.get,
                help=t("Which subtitles are burned into this video"),
                key=f"burn_mode_{video}",
            )
        if selected != mode:
            update_key(key, selected, add_missing=True)
            st.rerun()


def subtitle_style_settings():
    """Font, size and color of the burned-in subtitles; the other values of subtitle.style are edited in config.yaml."""
    from core.utils.subtitle_style import default_font, get_subtitle_style, save_subtitle_style, to_ass_color, to_hex_color
    with st.popover(t("Subtitle Style"), use_container_width=True):
        style = {}
        columns = st.columns(2)
        for column, kind, label in zip(columns, ("source", "translation"), (t("Source subtitles"), t("Translated subtitles"))):
            current = get_subtitle_style(kind)
            with column:
                st.markdown(f"**{label}**")
                font_name = st.text_input(
                    t("Font"), value=current["font_name"], placeholder=default_font(), key=f"subtitle_font_{kind}",
                    help=t("Name of a font installed on this computer, empty for the default font"))
                font_size = st.number_input(
                    t("Font size"), min_value=1, max_value=100, value=int(current["font_size"]), key=f"subtitle_size_{kind}")
                color = st.color_picker(t("Font color"), value=to_hex_color(current["font_color"]), key=f"subtitle_color_{kind}")
            # The transparency of the configured color is kept as long as the color is
            font_color = current["font_color"] if color == to_hex_color(current["font_color"]) else to_ass_color(color)
            style[kind] = {**current, "font_name": font_name.strip(), "font_size": font_size, "font_color": font_color}
        if style != {kind: get_subtitle_style(kind) for kind in style}:
            save_subtitle_style(style)
            st.rerun()


# The languages shown first keep the order of the old dropdown
LANGUAGE_LABELS = {
    "en": "🇺🇸 English", "zh": "🇨🇳 简体中文", "es": "🇪🇸 Español", "ru": "🇷🇺 Русский",
    "fr": "🇫🇷 Français", "de": "🇩🇪 Deutsch", "it": "🇮🇹 Italiano", "ja": "🇯🇵 日本語",
    "yue": "🇭🇰 粵語", "ko": "🇰🇷 한국어", "pt": "🇵🇹 Português", "ar": "🇸🇦 العربية",
    "id": "🇮🇩 Bahasa Indonesia", "th": "🇹🇭 ไทย", "vi": "🇻🇳 Tiếng Việt", "tr": "🇹🇷 Türkçe",
    "hi": "🇮🇳 हिन्दी", "ms": "🇲🇾 Bahasa Melayu", "nl": "🇳🇱 Nederlands", "sv": "🇸🇪 Svenska",
    "da": "🇩🇰 Dansk", "fi": "🇫🇮 Suomi", "pl": "🇵🇱 Polski", "cs": "🇨🇿 Čeština",
    "fil": "🇵🇭 Filipino", "fa": "🇮🇷 فارسی", "el": "🇬🇷 Ελληνικά", "ro": "🇷🇴 Română",
    "hu": "🇭🇺 Magyar", "mk": "🇲🇰 Македонски",
}


def recognition_languages(configured=None):
    """Label -> code for the recognition language dropdown: every Qwen3-ASR language."""
    from core.asr_backend.qwen_asr_local import ISO_TO_QWEN

    langs = {"Auto": "auto"}
    for code in [*LANGUAGE_LABELS, *ISO_TO_QWEN]:
        if code in ISO_TO_QWEN and code not in langs.values():
            langs[LANGUAGE_LABELS.get(code, ISO_TO_QWEN[code])] = code
    # A code set by hand in config.yaml (WhisperX and ElevenLabs know more languages) stays selectable
    if configured not in langs.values():
        langs[str(configured)] = configured
    return langs


def _fetch_model_list(base_url, api_key):
    """Fetch available models from OpenAI-compatible /v1/models endpoint."""
    if not base_url or (not api_key and not is_local_endpoint(base_url)):
        return []
    url = normalize_base_url(base_url) + "/models"
    try:
        resp = requests.get(
            url, headers={"Authorization": f"Bearer {api_key}"} if api_key else {}, timeout=10
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
                    is_valid, error = check_api()
                show_api_check(is_valid, error)
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
                    is_valid, error = check_api()
                    show_api_check(is_valid, error)
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
            langs = recognition_languages(load_key("whisper.language"))
            lang = st.selectbox(
                t("Recog Lang"),
                options=list(langs.keys()),
                index=list(langs.values()).index(load_key("whisper.language")),
            )
            if langs[lang] != load_key("whisper.language"):
                update_key("whisper.language", langs[lang])
                st.rerun()

        runtimes = ["local", "elevenlabs", "mai"]
        configured_runtime = load_key("whisper.runtime")
        if configured_runtime not in runtimes:
            st.warning(t("The 302.ai WhisperX cloud service has been retired. Select Local or ElevenLabs to continue."))
        runtime = st.selectbox(
            t("ASR Runtime"),
            options=runtimes,
            index=runtimes.index(configured_runtime) if configured_runtime in runtimes else None,
            format_func=lambda x: {
                "local": t("Local"),
                "elevenlabs": t("ElevenLabs"),
                "mai": t("MAI-Transcribe-2"),
            }[x],
            help=t(
                "Local Qwen3-ASR runs best on an NVIDIA GPU or Apple Silicon (CPU works but is slow); cloud recognition requires a provider API key."
            ),
        )
        if runtime is not None and runtime != configured_runtime:
            update_key("whisper.runtime", runtime)
            st.rerun()
        if runtime == "local":
            backends = ["qwen", "whisperx"]
            configured_backend = load_key_or("whisper.backend", "qwen")
            backend = st.selectbox(
                t("Local ASR Backend"),
                options=backends,
                index=backends.index(configured_backend) if configured_backend in backends else 0,
                format_func=lambda x: {
                    "qwen": t("Qwen3-ASR + ForcedAligner (default)"),
                    "whisperx": t("WhisperX (manual install)"),
                }[x],
            )
            if backend != configured_backend:
                update_key("whisper.backend", backend, add_missing=True)
                st.rerun()
            if backend == "whisperx" and importlib.util.find_spec("whisperx") is None:
                st.warning(t("WhisperX is not installed. Follow the manual page (docs/pages/docs/whisperx-manual.en-US.md) and install the extra packages yourself, or set whisper.backend to qwen."))
        if runtime == "elevenlabs":
            config_input(t("ElevenLabs API"), "whisper.elevenlabs_api_key")
        elif runtime == "mai":
            from core.asr_backend.mai_asr import detect_region

            configured_provider = str(load_key_or("whisper.mai_provider", "azure") or "azure").lower()
            providers = ["azure", "openrouter"]
            provider = st.selectbox(
                t("MAI provider"), options=providers,
                index=providers.index(configured_provider) if configured_provider in providers else 0,
                format_func=lambda value: "Azure Speech" if value == "azure" else "OpenRouter",
            )
            if provider != configured_provider:
                update_key("whisper.mai_provider", provider, add_missing=True)
                st.rerun()
            if provider == "openrouter":
                stored_key = str(load_key_or("whisper.mai_openrouter_api_key", "") or "")
                router_key = st.text_input(
                    t("OpenRouter API key"), value=stored_key, type="password",
                )
                if router_key != stored_key:
                    update_key("whisper.mai_openrouter_api_key", router_key, add_missing=True)
                st.caption(t("Audio is sent to OpenRouter for MAI-Transcribe-2 and may incur charges."))
            else:
                stored_key = str(load_key_or("whisper.mai_api_key", "") or "")
                speech_key = st.text_input(
                    t("Azure Speech key"), value=stored_key, type="password",
                    help=t("Use a key from an Azure Speech resource in a region where MAI-Transcribe-2 is available."),
                )
                if speech_key != stored_key:
                    update_key("whisper.mai_api_key", speech_key, add_missing=True)
                stored_region = str(load_key_or("whisper.mai_region", "") or "")
                region = st.text_input(
                    t("Azure Speech region or resource endpoint"), value=stored_region,
                    help=t("Enter a region such as eastus, or the HTTPS endpoint of your Azure Speech resource. Leave blank to detect the region from the key."),
                )
                if region != stored_region:
                    update_key("whisper.mai_region", region.strip(), add_missing=True)
                if st.button(t("Detect Azure Speech region"), disabled=not speech_key.strip()):
                    with st.spinner(t("Detecting Azure Speech region...")):
                        detected = detect_region(speech_key.strip())
                    if detected:
                        update_key("whisper.mai_region", detected, add_missing=True)
                        st.rerun()
                    else:
                        st.warning(t("Region detection failed. Check the key or enter the resource region manually."))
                st.caption(t("MAI-Transcribe-2 is in public preview. Audio is sent to Azure Speech."))

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

        configured_style = str(load_key_or("translation_style", "") or "")
        translation_style = st.text_input(
            t("Translation style"),
            value=configured_style,
            placeholder=t("e.g. colloquial, short sentences"),
            help=t("Optional. Describe the style of the translation in your own words, it is added to the translation prompt"),
        )
        if translation_style != configured_style:
            update_key("translation_style", translation_style, add_missing=True)
            st.rerun()

        demucs_available = importlib.util.find_spec("demucs") is not None
        if not demucs_available and load_key("demucs"):
            update_key("demucs", False)
        demucs = st.toggle(
            t("Vocal separation enhance"),
            value=load_key("demucs"),
            disabled=not demucs_available,
            help=t("Vocal separation is unavailable in this installation") if not demucs_available else t(
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
            if burn_subtitles:
                burned_subtitles_settings()
                subtitle_style_settings()

        pause_before_translate = st.toggle(
            t("Pause before translation"),
            value=load_key("pause_before_translate"),
            help=t("Pause after the terminology is extracted, so that you can edit `output/log/terminology.json` before the translation starts"),
        )
        if pause_before_translate != load_key("pause_before_translate"):
            update_key("pause_before_translate", pause_before_translate)
            st.rerun()

        pause_after_translate = st.toggle(
            t("Pause after translation"),
            value=bool(load_key_or("pause_after_translate", False)),
            help=t("Pause after the translation, so that you can edit the `Translation` column of `output/log/translation_results.xlsx` before the subtitles are generated"),
        )
        if pause_after_translate != bool(load_key_or("pause_after_translate", False)):
            update_key("pause_after_translate", pause_after_translate, add_missing=True)
            st.rerun()
    with st.expander(t("Dubbing Settings"), expanded=True):
        tts_method_labels = {
            "openai_tts": t("OpenAI TTS"),
            "fish_audio": t("Fish Audio"),
            "sf_fish_tts": t("SiliconFlow Fish TTS"),
            "edge_tts": t("Edge TTS"),
            "gpt_sovits": t("GPT-SoVITS"),
            "custom_tts": t("Custom TTS"),
            "sf_cosyvoice2": t("SiliconFlow CosyVoice2"),
            "f5tts": t("F5-TTS"),
            "voxcpm": t("ModelBest VoxCPM"),
        }
        from core.st_utils.tts_settings import select_tts_method
        select_tts = select_tts_method(tts_method_labels)

        # sub settings for each tts method
        if select_tts == "sf_fish_tts":

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
            config_input(t("OpenAI Voice"), "openai_tts.voice")

        elif select_tts == "fish_audio":
            from core.st_utils.tts_settings import save_settings
            from core.tts_backend.fish_audio_tts import voice_id_of
            mode_options = {
                "clone": t("Voice of the video"),
                "preset": t("Fixed voice"),
            }
            current_mode = load_key_or("fish_audio.mode", "clone")
            selected_mode = st.selectbox(
                t("Mode Selection"),
                options=list(mode_options.keys()),
                format_func=lambda x: mode_options[x],
                index=list(mode_options.keys()).index(current_mode) if current_mode in mode_options else 0,
            )
            if selected_mode != current_mode:
                save_settings({"fish_audio.mode": selected_mode})
                st.rerun()
            if selected_mode == "preset":
                voices = dict(load_key_or("fish_audio.voices", None) or {})
                voice_id = str(load_key_or("fish_audio.voice_id", "") or "")
                other = t("Another voice of fish.audio")
                names = list(voices) + [other]
                listed = next((name for name, listed_id in voices.items() if listed_id == voice_id), other)
                # The key keeps "Another voice" selected while its field is still empty
                selected_voice = st.selectbox(t("Voice"), names, index=names.index(listed), key="fish_audio_voice")
                if selected_voice == other:
                    entered = st.text_input(t("Voice ID or the address of its page"),
                                            value="" if voice_id in voices.values() else voice_id,
                                            help=t("Open a voice on fish.audio and copy the address of its page"))
                    selected_id = voice_id_of(entered)
                else:
                    selected_id = voices[selected_voice]
                if selected_id and selected_id != voice_id:
                    save_settings({"fish_audio.voice_id": selected_id})

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
    """Returns (is_valid, error): one request without retries, never answered from the cache."""
    try:
        resp = ask_gpt.__wrapped__(
            f"This is a test ({time.time():.0f}), response 'message':'success' in json format.",
            resp_type="json",
            log_title="None",
        )
        if resp.get("message") == "success":
            return True, ""
        return False, f"Unexpected response: {str(resp)[:300]}"
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:500]}"


def show_api_check(is_valid, error):
    if is_valid:
        st.toast(t("API Key is valid"), icon="✅")
    else:
        st.toast(t("API check failed"), icon="❌")
        st.error(f"{t('API check failed')}: {error}")


if __name__ == "__main__":
    check_api()
