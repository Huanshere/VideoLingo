"""The single processing plan used by the UI and API."""
from functools import partial
from importlib import import_module
from pathlib import Path

from core.task_runner import TaskRunner
from core.utils.models import _TEXT_DONE_MARKER, _AUDIO_DONE_MARKER


# Labels remain translation keys; only the UI translates them.
SUBTITLE_STEPS = [
    ("Word-level transcription and alignment", ("_2_asr.transcribe",)),
    ("Sentence segmentation using NLP and LLM", (
        "_3_1_split_nlp.split_by_spacy", "_3_2_split_meaning.split_sentences_by_meaning")),
    ("Summarization and multi-step translation", (
        "_4_1_summarize.get_summary", "_4_2_translate.translate_all")),
    ("Cutting and aligning long subtitles", (
        "_5_split_sub.split_for_sub_main", "_6_gen_sub.align_timestamp_main")),
    ("Merging subtitles into the video", ("_7_sub_into_vid.merge_subtitles_to_video",)),
]
DUBBING_STEPS = [
    ("Generate audio tasks and chunks", ("_8_1_audio_task.gen_audio_task_main", "_8_2_dub_chunks.gen_dub_chunks")),
    ("Extract reference audio", ("_9_refer_audio.extract_refer_audio_main",)),
    ("Generate and merge audio files", ("_10_gen_audio.gen_audio",)),
    ("Merge full audio", ("_11_merge_audio.merge_full_audio",)),
    ("Merge final audio into video", ("_12_dub_to_vid.merge_video_audio",)),
]


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
    if stage not in {"subtitles", "dubbing", "all"}:
        raise ValueError(f"Unknown stage: {stage}")
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
