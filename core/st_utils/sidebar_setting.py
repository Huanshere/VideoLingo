import importlib.util
import time
import streamlit as st
import requests
from translations.translations import translate as t
from core.utils import *
from core.utils.ask_gpt import is_local_endpoint, normalize_base_url


def config_input(label, key, help=None, placeholder=None):
    """Generic config input handler"""
    val = st.text_input(label, value=load_key(key), help=help, placeholder=placeholder)
    if val != load_key(key):
        update_key(key, val)
    return val


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
        """<style>[data-testid="stSidebar"] {min-width: 420px; max-width: 420px;}</style>""",
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

        runtimes = ["local", "elevenlabs"]
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
            }[x],
            help=t(
                "Local Qwen3-ASR runs best on an NVIDIA GPU or Apple Silicon (CPU works but is slow); ElevenLabs runtime requires an ElevenLabs API key."
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
            if backend == "qwen":
                sizes = ["1.7b", "0.6b"]
                configured_size = load_key_or("whisper.qwen_model", "1.7b")
                size = st.selectbox(
                    t("Qwen3-ASR Model Size"),
                    options=sizes,
                    index=sizes.index(configured_size) if configured_size in sizes else 0,
                    format_func=lambda x: {
                        "1.7b": t("1.7B (more accurate)"),
                        "0.6b": t("0.6B (faster, less memory)"),
                    }[x],
                )
                if size != configured_size:
                    update_key("whisper.qwen_model", size, add_missing=True)
                    st.rerun()
            elif importlib.util.find_spec("whisperx") is None:
                st.warning(t("WhisperX is not installed. Follow the manual page (docs/pages/docs/whisperx-manual.en-US.md) and install the extra packages yourself, or set whisper.backend to qwen."))
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

        pause_before_translate = st.toggle(
            t("Pause before translation"),
            value=load_key("pause_before_translate"),
            help=t("Pause after the terminology is extracted, so that you can edit `output/log/terminology.json` before the translation starts"),
        )
        if pause_before_translate != load_key("pause_before_translate"):
            update_key("pause_before_translate", pause_before_translate)
            st.rerun()
    with st.expander(t("Dubbing Settings"), expanded=True):
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

        elif select_tts == "fish_tts":
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
