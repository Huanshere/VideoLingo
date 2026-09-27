import os, sys, time


def _configure_utf8_console():
    """Allow Rich and task threads to print Unicode on Windows."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


_configure_utf8_console()

from runtime_libraries import configure_ffmpeg
configure_ffmpeg(required=True)

import streamlit as st
from core.st_utils.imports_and_utils import *
from core.task_runner import TaskRunner
from core.pipeline import get_steps
from core.utils import load_key, update_key
from core.utils.onekeycleanup import cleanup
from core.utils.delete_retry_dubbing import delete_dubbing_files
from translations.translations import DISPLAY_LANGUAGES, init_display_language, set_display_language
from core.utils.models import _TEXT_DONE_MARKER, _AUDIO_DONE_MARKER

# SET PATH
current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ["PATH"] += os.pathsep + current_dir
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(page_title="VideoLingo", page_icon="docs/logo.svg")

SUB_VIDEO = "output/output_sub.mp4"
DUB_VIDEO = "output/output_dub.mp4"


# ─── Task control UI (auto-refreshes every 1s while task is active) ───


@st.fragment(run_every=1)
def _task_control_panel(runner_key: str):
    """Renders progress bar + pause/stop buttons. Auto-refreshes every 1s."""
    runner = _get_runner(runner_key)

    if runner.state == "idle":
        return

    # Progress
    step_text = (
        f"({runner.current_step + 1}/{runner.total_steps}) {t(runner.current_label)}"
        if runner.current_step >= 0
        else ""
    )

    if runner.is_active:
        if runner.state == "paused":
            st.warning(f"⏸️ {t('Paused')} {step_text}")
        else:
            st.info(f"⏳ {t('Running...')} {step_text}")
        st.progress(runner.progress)

        if runner.state == "stopping":
            st.info(t("Stopping..."))
            return

        # Control buttons
        col1, col2 = st.columns(2)
        with col1:
            if runner.state == "paused":
                if st.button(
                    f"▶️ {t('Resume')}",
                    key=f"{runner_key}_resume",
                    use_container_width=True,
                ):
                    runner.resume()
                    st.rerun()
            else:
                if st.button(
                    f"⏸️ {t('Pause')}",
                    key=f"{runner_key}_pause",
                    use_container_width=True,
                ):
                    runner.pause()
                    st.rerun()
        with col2:
            if st.button(
                f"⏹️ {t('Stop')}",
                key=f"{runner_key}_stop",
                use_container_width=True,
                type="primary",
            ):
                runner.stop()
                st.rerun()

    elif runner.state == "completed":
        st.success(t("Task completed!"))
        st.progress(1.0)
        runner.reset()
        time.sleep(0.5)
        st.rerun(scope="app")

    elif runner.state == "stopped":
        st.warning(f"⏹️ {t('Task stopped')} {step_text}")
        if st.button(t("OK"), key=f"{runner_key}_ack_stop", use_container_width=True):
            runner.reset()
            st.rerun(scope="app")

    elif runner.state == "error":
        st.error(f"❌ {t('Task error')}: {runner.error_msg}")
        if st.button(t("OK"), key=f"{runner_key}_ack_error", use_container_width=True):
            runner.reset()
            st.rerun(scope="app")


# ─── Text processing ───


def _get_runner(key):
    if key not in st.session_state:
        st.session_state[key] = TaskRunner()
    return st.session_state[key]


def _clear_path(path):
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


def _subtitle_length_controls():
    """Render inline controls for the two subtitle-length tunables.

    Both values live in config.yaml and are read by:
      - max_split_length    → core/_3_2_split_meaning.py (first pass NLP cut)
      - subtitle.max_length → core/_5_split_sub.py       (final subtitle line)
    """
    DEFAULT_MAX_SPLIT_LENGTH = 20
    DEFAULT_MAX_LENGTH = 75
    MAX_LENGTH_KEY = "subtitle.max_length"

    with st.expander(t("Subtitle length tuning"), expanded=False):
        st.caption(
            t(
                "These two values control how subtitles are cut. "
                "Smaller = more, shorter lines. Larger = fewer, longer lines."
            )
        )

        new_max_split = st.number_input(
            t("max_split_length (rough cut, words/tokens per chunk)"),
            min_value=8,
            max_value=60,
            value=int(load_key("max_split_length")),
            step=1,
            help=t(
                "Suggested: 18-25. Below 18 cuts too finely and hurts translation; "
                "above 25 makes downstream subtitle splitting hard to align."
            ),
            key="cfg_max_split_length",
            width=220,
        )
        new_max_length = st.number_input(
            t("max_length (max characters per subtitle line)"),
            min_value=20,
            max_value=200,
            value=int(load_key(MAX_LENGTH_KEY)),
            step=1,
            help=t(
                "Suggested: 50-90. Lower if a subtitle line looks crowded on screen; "
                "raise if lines are split too aggressively."
            ),
            key="cfg_max_length",
            width=220,
        )

        changed = False
        if new_max_split != load_key("max_split_length"):
            update_key("max_split_length", int(new_max_split))
            changed = True
        if new_max_length != load_key(MAX_LENGTH_KEY):
            update_key(MAX_LENGTH_KEY, int(new_max_length))
            changed = True

        if st.button(
            t("Restore defaults ({split}/{length})")
            .replace("{split}", str(DEFAULT_MAX_SPLIT_LENGTH))
            .replace("{length}", str(DEFAULT_MAX_LENGTH)),
            key="restore_subtitle_length_defaults",
        ):
            update_key("max_split_length", DEFAULT_MAX_SPLIT_LENGTH)
            update_key(MAX_LENGTH_KEY, DEFAULT_MAX_LENGTH)
            st.rerun()

        if changed:
            st.rerun()


def text_processing_section():
    st.header(t("b. Translate and Generate Subtitles"))
    runner = _get_runner("_text_runner")
    from core._1_ytdlp import is_audio_only_input
    audio_only = is_audio_only_input()

    with st.container(border=True):
        final_text_step = t("Generate subtitle files") if audio_only else t("Merging subtitles into the video")
        st.markdown(
            f"""
        <p style='font-size: 20px;'>
        {t("This stage includes the following steps:")}
        <p style='font-size: 20px;'>
            1. {t("Word-level transcription and alignment")}<br>
            2. {t("Sentence segmentation using NLP and LLM")}<br>
            3. {t("Summarization and multi-step translation")}<br>
            4. {t("Cutting and aligning long subtitles")}<br>
            5. {final_text_step}
        """,
            unsafe_allow_html=True,
        )

        text_done = os.path.exists(_TEXT_DONE_MARKER) or (
            os.path.exists("output/trans.srt")
            and os.path.exists("output/src.srt")
            and (audio_only or os.path.exists(SUB_VIDEO))
        )

        if runner.is_active or runner.is_done or not text_done:
            if runner.is_active:
                _task_control_panel("_text_runner")
            elif runner.is_done:
                _task_control_panel("_text_runner")
            else:
                _subtitle_length_controls()
                if st.button(
                    t("Start Processing Subtitles"), key="text_processing_button"
                ):
                    steps = get_steps("subtitles")
                    runner.start(steps)
                    st.rerun()
        else:
            if not audio_only and load_key("burn_subtitles") and os.path.exists(SUB_VIDEO):
                st.video(SUB_VIDEO)
            download_subtitle_zip_button(text=t("Download All Srt Files"))

            if st.button(t("Archive to 'history'"), key="cleanup_in_text_processing"):
                cleanup()
                st.rerun()
            return True


# ─── Audio processing ───


def audio_processing_section():
    from core._1_ytdlp import is_audio_only_input
    audio_only = is_audio_only_input()
    st.header(t("c. Dubbing"))
    runner = _get_runner("_audio_runner")

    with st.container(border=True):
        st.markdown(
            f"""
        <p style='font-size: 20px;'>
        {t("This stage includes the following steps:")}
        <p style='font-size: 20px;'>
            1. {t("Generate audio tasks and chunks")}<br>
            2. {t("Extract reference audio")}<br>
            3. {t("Generate and merge audio files")}<br>
            4. {t("Merge full audio")}<br>
            5. {t("Merge final audio into video")}
        """,
            unsafe_allow_html=True,
        )

        audio_done = os.path.exists(_AUDIO_DONE_MARKER) or (
            os.path.exists("output/dub.mp3")
            and (audio_only or os.path.exists(DUB_VIDEO))
        )
        if runner.is_active or runner.is_done or not audio_done:
            if runner.is_active:
                _task_control_panel("_audio_runner")
            elif runner.is_done:
                _task_control_panel("_audio_runner")
            else:
                if st.button(
                    t("Start Audio Processing"), key="audio_processing_button"
                ):
                    steps = get_steps("dubbing")
                    runner.start(steps)
                    st.rerun()
        else:
            st.success(
                t(
                    "Audio processing is complete! You can check the audio files in the `output` folder."
                )
            )
            if not audio_only and os.path.exists(DUB_VIDEO):
                st.video(DUB_VIDEO)
            if st.button(t("Delete dubbing files"), key="delete_dubbing_files"):
                _clear_path(_AUDIO_DONE_MARKER)
                delete_dubbing_files()
                st.rerun()
            if st.button(t("Archive to 'history'"), key="cleanup_in_audio_processing"):
                cleanup()
                st.rerun()


# ─── Main ───


def main():
    init_display_language()
    st.set_option("client.toolbarMode", "viewer")

    logo_col, lang_col = st.columns([3, 1])
    with logo_col:
        st.image("docs/logo.png", width="stretch")
    with lang_col:
        language_values = list(DISPLAY_LANGUAGES.values())
        current_language = init_display_language()
        selected_language = st.selectbox(
            t("Display Language 🌐"),
            options=list(DISPLAY_LANGUAGES.keys()),
            index=language_values.index(current_language) if current_language in language_values else 0,
            key="display_language_selector",
        )
        new_language = DISPLAY_LANGUAGES[selected_language]
        if new_language != current_language:
            set_display_language(new_language)
            st.rerun()

    st.markdown(button_style, unsafe_allow_html=True)
    welcome_text = t(
        'Welcome to VideoLingo! 👋 You can also try it online at <a href="https://videolingo.io" target="_blank">videolingo.io</a>.'
    )
    st.markdown(
        f"<p style='font-size: 20px; color: #808080;'>{welcome_text}</p>",
        unsafe_allow_html=True,
    )
    # add settings
    with st.sidebar:
        page_setting()
        st.markdown(give_star_button(), unsafe_allow_html=True)
    if download_video_section():
        text_done = text_processing_section()
        from core._1_ytdlp import is_audio_only_input
        if text_done and not is_audio_only_input():
            audio_processing_section()


if __name__ == "__main__":
    main()
