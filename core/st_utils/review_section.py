from __future__ import annotations

import pandas as pd
import streamlit as st

from core import review, workspace
from translations.translations import translate as t


STAGE_LABELS = {
    "terminology": "Terminology",
    "translation": "Translation",
    "subtitles": "Subtitles",
    "tts_text": "TTS Text",
}

STATUS_ICON = {
    "pending": "○",
    "confirmed": "✓",
    "stale": "!",
}


def render_status_row() -> None:
    status = review.load_status()
    cols = st.columns(4)
    for column, stage in zip(cols, review.STAGES):
        item = status["stages"][stage]
        icon = STATUS_ICON.get(item["status"], "○")
        column.metric(t(STAGE_LABELS[stage]), f"{icon} {t(item['status'])}")


def _missing_artifact(stage: str) -> bool:
    path = review.artifact_path(stage)
    if path.exists():
        return False
    st.info(t("Waiting for the upstream step to generate this review file."))
    st.caption(str(path))
    return True


def _confirm_controls(stage: str) -> None:
    col1, col2 = st.columns(2)
    with col1:
        if st.button(t("Confirm"), key=f"review_confirm_{stage}", width="stretch"):
            review.mark_confirmed(stage)
            st.rerun()
    with col2:
        if st.button(
            t("Mark as needs review"),
            key=f"review_pending_{stage}",
            width="stretch",
        ):
            review.mark_needs_review(stage)
            st.rerun()


def terminology_tab() -> None:
    stage = "terminology"
    if _missing_artifact(stage):
        return
    try:
        data = review.load_terminology()
    except Exception as exc:
        st.error(f"{t('Unable to load review file')}: {exc}")
        return

    theme = st.text_area(t("Theme"), value=str(data.get("theme", "")), key="review_theme")
    terms = pd.DataFrame(data.get("terms", []), columns=["src", "tgt", "note"])
    edited = st.data_editor(
        terms,
        num_rows="dynamic",
        width="stretch",
        key="review_terms_editor",
    )
    if st.button(t("Save changes"), key="review_save_terminology", width="stretch"):
        review.save_terminology(edited.fillna("").to_dict("records"), theme=theme)
        st.success(t("Saved"))
        st.rerun()
    _confirm_controls(stage)


def table_tab(
    stage: str,
    required_columns: tuple[str, ...],
    editable_columns: tuple[str, ...],
) -> None:
    if _missing_artifact(stage):
        return
    try:
        df = review.load_table(stage)
    except Exception as exc:
        st.error(f"{t('Unable to load review file')}: {exc}")
        return

    disabled = [column for column in df.columns if column not in editable_columns]
    edited = st.data_editor(
        df,
        disabled=disabled,
        width="stretch",
        hide_index=False,
        key=f"review_editor_{stage}",
    )
    if st.button(t("Save changes"), key=f"review_save_{stage}", width="stretch"):
        if stage == "subtitles":
            review.save_subtitles(edited)
        else:
            review.save_table(stage, edited, required_columns=required_columns)
        st.success(t("Saved"))
        st.rerun()
    _confirm_controls(stage)


def review_section() -> None:
    st.header(t("Review Workbench"))
    if not workspace.get_active_workspace():
        st.info(t("Create or select a task workspace before reviewing."))
        return

    render_status_row()
    tab_terms, tab_translation, tab_subtitles, tab_tts = st.tabs(
        [
            t("Terminology"),
            t("Translation"),
            t("Subtitles"),
            t("TTS Text"),
        ]
    )
    with tab_terms:
        terminology_tab()
    with tab_translation:
        table_tab(
            "translation",
            required_columns=("Source", "Translation"),
            editable_columns=("Translation",),
        )
    with tab_subtitles:
        table_tab(
            "subtitles",
            required_columns=("Source", "Translation"),
            editable_columns=("Source", "Translation"),
        )
    with tab_tts:
        table_tab(
            "tts_text",
            required_columns=(
                "number",
                "start_time",
                "end_time",
                "duration",
                "text",
                "origin",
            ),
            editable_columns=("text", "origin"),
        )
