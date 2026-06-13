import os, sys, time


def _configure_utf8_console():
    """Allow Rich and task threads to print Unicode on Windows."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


_configure_utf8_console()

import streamlit as st
from core.st_utils.imports_and_utils import *
from core.st_utils.review_section import review_section
from core.st_utils.task_runner import TaskRunner
from core import *
from core import review, workspace

# SET PATH
current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ["PATH"] += os.pathsep + current_dir
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(page_title="VideoLingo", page_icon="docs/logo.svg")


# ─── Task control UI (auto-refreshes every 1s while task is active) ───


def _sub_video_path():
    return str(workspace.output_path("output_sub.mp4"))


def _dub_video_path():
    return str(workspace.output_path("output_dub.mp4"))


@st.fragment(run_every=1)
def _task_control_panel(runner_key: str):
    """Renders progress bar + pause/stop buttons. Auto-refreshes every 1s."""
    runner = TaskRunner.get(st.session_state, runner_key)

    if runner.state == "idle":
        return

    # Progress
    step_text = (
        f"({runner.current_step + 1}/{runner.total_steps}) {runner.current_label}"
        if runner.current_step >= 0
        else ""
    )

    if runner.is_active:
        if runner.state == "paused":
            st.warning(f"⏸️ {t('Paused')} {step_text}")
        else:
            st.info(f"⏳ {t('Running...')} {step_text}")
        st.progress(runner.progress)

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


def _stage_confirmed(stage: str) -> bool:
    try:
        status = review.load_status()
        return status["stages"][stage]["status"] == "confirmed"
    except Exception:
        return False


def _artifact_exists(stage: str) -> bool:
    try:
        return review.artifact_path(stage).exists()
    except Exception:
        return False


def _get_text_generation_steps():
    return [
        (t("WhisperX word-level transcription"), _2_asr.transcribe),
        (
            t("Sentence segmentation using NLP and LLM"),
            lambda: (
                _3_1_split_nlp.split_by_spacy(),
                _3_2_split_meaning.split_sentences_by_meaning(),
            ),
        ),
        (t("Summarization and terminology generation"), _4_1_summarize.get_summary),
    ]


def _get_translation_steps():
    return [(t("Multi-step translation"), _4_2_translate.translate_all)]


def _get_subtitle_split_steps():
    return [(t("Cutting and aligning long subtitles"), _5_split_sub.split_for_sub_main)]


def _get_subtitle_finalize_steps():
    return [
        (t("Generating timeline and subtitles"), _6_gen_sub.align_timestamp_main),
        (t("Merging subtitles into the video"), _7_sub_into_vid.merge_subtitles_to_video),
    ]


def text_processing_section():
    st.header(t("b. Translate and Generate Subtitles"))
    runner = TaskRunner.get(st.session_state, "_text_runner")
    sub_video = _sub_video_path()

    with st.container(border=True):
        st.markdown(
            f"""
        <p style='font-size: 20px;'>
        {t("This stage includes the following steps:")}
        <p style='font-size: 20px;'>
            1. {t("WhisperX word-level transcription")}<br>
            2. {t("Sentence segmentation using NLP and LLM")}<br>
            3. {t("Generate terminology for review")}<br>
            4. {t("Review terminology, translation, and subtitles")}<br>
            5. {t("Generating timeline and subtitles")}<br>
            6. {t("Merging subtitles into the video")}
        """,
            unsafe_allow_html=True,
        )

        if not os.path.exists(sub_video):
            if runner.is_active:
                _task_control_panel("_text_runner")
            elif runner.is_done:
                _task_control_panel("_text_runner")
            elif not _artifact_exists("terminology"):
                if st.button(
                    t("Generate terminology for review"),
                    key="generate_terms_button",
                ):
                    runner.start(_get_text_generation_steps())
                    st.rerun()
            elif not _stage_confirmed("terminology"):
                st.info(t("Review and confirm terminology before translation."))
            elif not _artifact_exists("translation"):
                if st.button(
                    t("Continue to translation"),
                    key="continue_translation_button",
                ):
                    runner.start(_get_translation_steps())
                    st.rerun()
            elif not _stage_confirmed("translation"):
                st.info(t("Review and confirm translation before subtitle splitting."))
            elif not _artifact_exists("subtitles"):
                if st.button(
                    t("Generate subtitle split for review"),
                    key="continue_subtitle_split_button",
                ):
                    runner.start(_get_subtitle_split_steps())
                    st.rerun()
            elif not _stage_confirmed("subtitles"):
                st.info(
                    t("Review and confirm subtitles before final subtitle generation.")
                )
            else:
                if st.button(
                    t("Generate final subtitles and video"),
                    key="continue_subtitle_finalize_button",
                ):
                    runner.start(_get_subtitle_finalize_steps())
                    st.rerun()
        else:
            if load_key("burn_subtitles"):
                st.video(sub_video)
            download_subtitle_zip_button(text=t("Download All Srt Files"))

            if st.button(t("Archive to 'history'"), key="cleanup_in_text_processing"):
                cleanup()
                st.rerun()
            return True


# ─── Audio processing ───


def _get_tts_task_steps():
    return [(t("Generate audio tasks"), _8_1_audio_task.gen_audio_task_main)]


def _get_audio_finalize_steps():
    return [
        (t("Generate audio chunks"), _8_2_dub_chunks.gen_dub_chunks),
        (t("Extract reference audio"), _9_refer_audio.extract_refer_audio_main),
        (t("Generate and merge audio files"), _10_gen_audio.gen_audio),
        (t("Merge full audio"), _11_merge_audio.merge_full_audio),
        (t("Merge final audio into video"), _12_dub_to_vid.merge_video_audio),
    ]


def audio_processing_section():
    st.header(t("c. Dubbing"))
    runner = TaskRunner.get(st.session_state, "_audio_runner")
    dub_video = _dub_video_path()

    with st.container(border=True):
        st.markdown(
            f"""
        <p style='font-size: 20px;'>
        {t("This stage includes the following steps:")}
        <p style='font-size: 20px;'>
            1. {t("Generate audio tasks and chunks")}<br>
            2. {t("Review and confirm TTS text")}<br>
            3. {t("Extract reference audio")}<br>
            4. {t("Generate and merge audio files")}<br>
            5. {t("Merge final audio into video")}
        """,
            unsafe_allow_html=True,
        )

        if not os.path.exists(dub_video):
            if runner.is_active:
                _task_control_panel("_audio_runner")
            elif runner.is_done:
                _task_control_panel("_audio_runner")
            elif not _artifact_exists("tts_text"):
                if st.button(
                    t("Generate TTS text for review"),
                    key="generate_tts_text_button",
                ):
                    runner.start(_get_tts_task_steps())
                    st.rerun()
            elif not _stage_confirmed("tts_text"):
                st.info(t("Review and confirm TTS text before dubbing."))
            else:
                if st.button(
                    t("Generate dubbing"), key="continue_audio_finalize_button"
                ):
                    runner.start(_get_audio_finalize_steps())
                    st.rerun()
        else:
            st.success(
                t(
                    "Audio processing is complete! You can check the audio files in the `output` folder."
                )
            )
            if load_key("burn_subtitles"):
                st.video(dub_video)
            if st.button(t("Delete dubbing files"), key="delete_dubbing_files"):
                delete_dubbing_files()
                st.rerun()
            if st.button(t("Archive to 'history'"), key="cleanup_in_audio_processing"):
                cleanup()
                st.rerun()


# ─── Main ───


def workspace_section():
    st.header(t("Task Workspace"))

    if st.session_state.get("_active_workspace"):
        try:
            workspace.set_active_workspace(st.session_state["_active_workspace"])
        except FileNotFoundError:
            st.session_state.pop("_active_workspace", None)
            workspace.clear_active_workspace()

    jobs = workspace.list_jobs()
    labels = [f"{job['name']} · {job['status']} · {job['id']}" for job in jobs]
    selected = st.selectbox(t("Continue task"), [""] + labels)
    if selected:
        job = jobs[labels.index(selected)]
        workspace.set_active_workspace(job["path"])
        st.session_state["_active_workspace"] = job["path"]

    new_name = st.text_input(t("New task name"), value="")
    if st.button(t("New task"), key="new_workspace_task", width="stretch"):
        job = workspace.create_job(name=new_name or "VideoLingo Task")
        workspace.set_active_workspace(job["path"])
        st.session_state["_active_workspace"] = job["path"]
        st.rerun()

    active = workspace.get_active_workspace()
    if active:
        job = workspace.load_job(active)
        st.caption(f"{job['name']} · {job['status']}")
        if st.button(t("Archive task"), key="archive_workspace_task", width="stretch"):
            workspace.archive_job(active)
            workspace.clear_active_workspace()
            st.session_state.pop("_active_workspace", None)
            st.rerun()


def main():
    logo_col, _ = st.columns([1, 1])
    with logo_col:
        st.image("docs/logo.png", width="stretch")
    st.markdown(button_style, unsafe_allow_html=True)
    welcome_text = t(
        'Hello, welcome to VideoLingo. If you encounter any issues, feel free to get instant answers with our Free QA Agent <a href="https://share.fastgpt.in/chat/share?shareId=066w11n3r9aq6879r4z0v9rh" target="_blank">here</a>! You can also try out our SaaS website at <a href="https://videolingo.io" target="_blank">videolingo.io</a> for free!'
    )
    st.markdown(
        f"<p style='font-size: 20px; color: #808080;'>{welcome_text}</p>",
        unsafe_allow_html=True,
    )
    # add settings
    with st.sidebar:
        workspace_section()
        page_setting()
        st.markdown(give_star_button, unsafe_allow_html=True)
    download_video_section()
    review_section()
    text_processing_section()
    audio_processing_section()


if __name__ == "__main__":
    main()
