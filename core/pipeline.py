"""The single processing plan used by the UI and API."""
from functools import partial
from importlib import import_module
import json
from pathlib import Path

from core.task_runner import TaskRunner
from core.utils.config_utils import load_key, load_key_or
from core.utils.models import _4_1_TERMINOLOGY, _4_2_TRANSLATION, _5_SPLIT_SUB, _TEXT_DONE_MARKER, _AUDIO_DONE_MARKER


# Labels remain translation keys; only the UI translates them.
SUBTITLE_STEPS = [
    ("Word-level transcription and alignment", ("_2_import_subtitles.import_subtitles", "_2_asr.transcribe")),
    ("Sentence segmentation using NLP and LLM", (
        "_3_1_split_nlp.split_by_spacy", "_3_2_split_meaning.split_sentences_by_meaning")),
    ("Summarization and multi-step translation", (
        "_4_1_summarize.get_summary", "pipeline.review_terminology", "_4_2_translate.translate_all",
        "pipeline.review_translation")),
    ("Cutting and aligning long subtitles", (
        "_5_split_sub.split_for_sub_main", "_6_gen_sub.align_timestamp_main")),
    ("Merging subtitles into the video", ("_7_sub_into_vid.merge_subtitles_to_video",)),
]
# Only the source subtitles: no translation and no video
TRANSCRIBE_STEPS = SUBTITLE_STEPS[:2] + [
    ("Generate subtitle files", ("_6_gen_sub.gen_source_subtitles",)),
]
DUBBING_STEPS = [
    ("Generate audio tasks and chunks", ("_8_1_audio_task.gen_audio_task_main", "_8_2_dub_chunks.gen_dub_chunks")),
    ("Extract reference audio", ("_9_refer_audio.extract_refer_audio_main",)),
    ("Generate and merge audio files", ("_10_gen_audio.gen_audio",)),
    ("Merge full audio", ("_11_merge_audio.merge_full_audio",)),
    ("Merge final audio into video", ("_12_dub_to_vid.merge_video_audio",)),
]


# These messages are translation keys as well
REVIEW_TERMINOLOGY = "Terminology is ready for review. Edit `output/log/terminology.json` if needed, then press Resume to start translating."
INVALID_TERMINOLOGY = "`output/log/terminology.json` can not be read after your edit. Fix it, then press Resume."
REVIEW_TRANSLATION = "Translation is ready for review. Edit the `Translation` column of `output/log/translation_results.xlsx` if needed, without changing the `Source` column or the number of rows. Save and close the file, then press Resume."
INVALID_TRANSLATION = "`output/log/translation_results.xlsx` can not be used after your edit. Keep the rows and the `Source` column as they were, leave no translation empty, and close the file. Then press Resume."


def terminology_error():
    """What is wrong with the terminology file, or None when the translation can use it."""
    try:
        terminology = json.loads(Path(_4_1_TERMINOLOGY).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return str(e)
    terms = terminology.get("terms") if isinstance(terminology, dict) else None
    if not isinstance(terms, list):
        return "`terms` must be a list"
    for term in terms:
        if not isinstance(term, dict) or not all(isinstance(term.get(key), str) for key in ("src", "tgt", "note")):
            return f"Each term needs the texts `src`, `tgt` and `note`: {term}"
    return None


def review_terminology():
    """Optional checkpoint `pause_before_translate`: the task waits until the user resumes it."""
    runner = TaskRunner._current
    if runner is None or not load_key("pause_before_translate") or Path(_4_2_TRANSLATION).exists():
        return
    message = REVIEW_TERMINOLOGY
    while True:
        runner.pause(message)
        TaskRunner.check_cancel()
        error = terminology_error()
        if error is None:
            return
        print(f"⚠️ {_4_1_TERMINOLOGY}: {error}")
        message = INVALID_TERMINOLOGY


def read_translation():
    """The source lines and the translated lines of the translation results, empty cells as ''."""
    import pandas as pd
    df = pd.read_excel(_4_2_TRANSLATION)
    return [["" if pd.isna(value) else str(value).strip() for value in df[column]] for column in ("Source", "Translation")]


def translation_error(source, translation):
    """What is wrong with the edited translation results, or None when the subtitles can use them."""
    try:
        edited_source, edited_translation = read_translation()
    except Exception as e:  # locked by the spreadsheet program, no longer a spreadsheet, a missing column
        return f"{type(e).__name__}: {e}"
    if edited_source != source:
        return "the rows or the `Source` column have changed"
    for row, (before, after) in enumerate(zip(translation, edited_translation), 2):
        if before and not after:
            return f"the translation in row {row} is empty"
    return None


def review_translation():
    """Optional checkpoint `pause_after_translate`: the task waits until the user resumes it."""
    runner = TaskRunner._current
    if runner is None or not load_key_or("pause_after_translate", False) or Path(_5_SPLIT_SUB).exists():
        return
    source, translation = read_translation()
    message = REVIEW_TRANSLATION
    while True:
        runner.pause(message)
        TaskRunner.check_cancel()
        error = translation_error(source, translation)
        if error is None:
            return
        print(f"⚠️ {_4_2_TRANSLATION}: {error}")
        message = INVALID_TRANSLATION


def _execute(calls, clear_marker=None):
    if clear_marker:
        Path(clear_marker).unlink(missing_ok=True)
    for call in calls:
        TaskRunner.check_cancel()
        module, function = call.split('.')
        getattr(import_module(f"core.{module}"), function)()


def _finish(marker):
    TaskRunner.check_cancel()
    Path(marker).parent.mkdir(parents=True, exist_ok=True)
    Path(marker).touch()


def get_steps(stage="subtitles", dubbing=False):
    """Build a fresh sequential plan. Existing intermediate files support retries."""
    if stage not in {"transcribe", "subtitles", "dubbing", "all"}:
        raise ValueError(f"Unknown stage: {stage}")
    if stage == "transcribe":
        return [(label, partial(_execute, calls)) for label, calls in TRANSCRIBE_STEPS]
    stages = []
    if stage in {"subtitles", "all"}:
        stages.append((SUBTITLE_STEPS, _TEXT_DONE_MARKER, "Finalize subtitle outputs"))
    if stage == "dubbing" or (stage == "all" and dubbing):
        stages.append((DUBBING_STEPS, _AUDIO_DONE_MARKER, "Finalize dubbing outputs"))
    steps = []
    for definitions, marker, final_label in stages:
        steps.extend((label, partial(_execute, calls, marker if i == 0 else None))
                     for i, (label, calls) in enumerate(definitions))
        steps.append((final_label, partial(_finish, marker)))
    return steps
