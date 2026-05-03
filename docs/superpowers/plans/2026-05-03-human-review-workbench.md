# Human Review Workbench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a workspace-local human review workbench for terminology, translation, subtitle rows, and TTS text.

**Architecture:** Add a focused `core/review.py` module that owns review status, artifact loading/saving, backups, and invalidation. Add `core/st_utils/review_section.py` for Streamlit UI, then wire `st.py` so text and audio workflows pause at review checkpoints and resume from the confirmed stage.

**Tech Stack:** Python, Streamlit, pandas Excel files, ruamel.yaml, JSON artifacts, existing VideoLingo workspace path helpers.

---

## File Structure

- Create `core/review.py`
  - Review stage metadata.
  - `review_status.yaml` creation/loading/saving.
  - Workspace-aware artifact paths.
  - JSON and Excel artifact read/write helpers.
  - Backups under `artifacts/reviews/backups/`.
  - Downstream invalidation rules.
- Create `core/st_utils/review_section.py`
  - Streamlit status row and four tabs.
  - Editable data tables for terminology, translation, subtitles, and TTS text.
  - Save, confirm, and mark-needs-review buttons.
- Modify `st.py`
  - Import review helpers.
  - Split text processing into review-aware step groups.
  - Split audio processing into review-aware step groups.
  - Render review workbench after download section.
  - Show action buttons for "generate next artifact", "review", and "continue".
- Modify `core/__init__.py`
  - Export `review`.
- Create `tests/test_review.py`
  - Unit tests for status, backups, artifact saves, and invalidation.
- Modify `tests/test_workspace.py` only if workspace setup needs a small helper; otherwise leave it unchanged.

---

### Task 1: Add Review Status Core

**Files:**
- Create: `core/review.py`
- Create: `tests/test_review.py`
- Modify: `core/__init__.py`

- [ ] **Step 1: Write failing tests for default review status and confirmations**

Add this to `tests/test_review.py`:

```python
import tempfile
import unittest
from pathlib import Path

from ruamel.yaml import YAML

from core import review, workspace


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config_path = self.root / "config.yaml"
        self.config_path.write_text("display_language: en\n", encoding="utf-8")
        self.job = workspace.create_job(
            name="Review Video",
            workspace_root=self.root / "jobs",
            config_path=self.config_path,
        )
        workspace.set_active_workspace(self.job["path"])

    def tearDown(self):
        workspace.clear_active_workspace()

    def test_default_review_status_is_created_in_active_workspace(self):
        status = review.load_status()

        status_path = Path(self.job["path"]) / "artifacts" / "reviews" / "review_status.yaml"
        self.assertTrue(status_path.is_file())
        self.assertEqual(status["stages"]["terminology"]["status"], "pending")
        self.assertEqual(
            status["stages"]["translation"]["artifact"],
            "output/log/translation_results.xlsx",
        )

    def test_mark_confirmed_records_timestamp(self):
        review.mark_confirmed("terminology")
        status = review.load_status()

        self.assertEqual(status["stages"]["terminology"]["status"], "confirmed")
        self.assertTrue(status["stages"]["terminology"]["confirmed_at"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
/Users/oliverchow/VideoLingo/.venv/bin/python -m unittest tests.test_review -v
```

Expected: fail because `core.review` does not exist.

- [ ] **Step 3: Implement minimal review status core**

Create `core/review.py`:

```python
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from core import workspace

REVIEW_ROOT = Path("artifacts") / "reviews"
BACKUP_DIR = REVIEW_ROOT / "backups"
STATUS_FILE = REVIEW_ROOT / "review_status.yaml"

STAGES = {
    "terminology": "output/log/terminology.json",
    "translation": "output/log/translation_results.xlsx",
    "subtitles": "output/log/translation_results_for_subtitles.xlsx",
    "tts_text": "output/audio/tts_tasks.xlsx",
}

DOWNSTREAM = {
    "terminology": ("translation", "subtitles", "tts_text"),
    "translation": ("subtitles", "tts_text"),
    "subtitles": ("tts_text",),
    "tts_text": (),
}

yaml = YAML()
yaml.preserve_quotes = True


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def active_workspace_dir() -> Path:
    active = workspace.get_active_workspace()
    if not active:
        raise RuntimeError("Select or create a task workspace before reviewing artifacts.")
    return Path(active)


def review_root() -> Path:
    return active_workspace_dir() / REVIEW_ROOT


def review_status_path() -> Path:
    return active_workspace_dir() / STATUS_FILE


def default_status() -> dict[str, Any]:
    return {
        "stages": {
            stage: {
                "status": "pending",
                "artifact": artifact,
                "confirmed_at": "",
                "updated_at": "",
            }
            for stage, artifact in STAGES.items()
        }
    }


def save_status(status: dict[str, Any]) -> None:
    path = review_status_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        yaml.dump(status, file)


def normalize_status(status: dict[str, Any] | None) -> dict[str, Any]:
    merged = default_status()
    for stage, values in (status or {}).get("stages", {}).items():
        if stage in merged["stages"] and isinstance(values, dict):
            merged["stages"][stage].update(values)
    return merged


def load_status() -> dict[str, Any]:
    path = review_status_path()
    if not path.exists():
        status = default_status()
        save_status(status)
        return status
    with open(path, "r", encoding="utf-8") as file:
        status = normalize_status(yaml.load(file) or {})
    save_status(status)
    return status


def validate_stage(stage: str) -> None:
    if stage not in STAGES:
        raise ValueError(f"Unknown review stage: {stage}")


def mark_confirmed(stage: str) -> dict[str, Any]:
    validate_stage(stage)
    status = load_status()
    stamp = now_iso()
    status["stages"][stage]["status"] = "confirmed"
    status["stages"][stage]["confirmed_at"] = stamp
    status["stages"][stage]["updated_at"] = stamp
    save_status(status)
    return status


def mark_needs_review(stage: str) -> dict[str, Any]:
    validate_stage(stage)
    status = load_status()
    status["stages"][stage]["status"] = "pending"
    status["stages"][stage]["confirmed_at"] = ""
    status["stages"][stage]["updated_at"] = now_iso()
    save_status(status)
    return status


def invalidate_downstream(stage: str, status: dict[str, Any] | None = None) -> dict[str, Any]:
    validate_stage(stage)
    status = status or load_status()
    stamp = now_iso()
    for downstream in DOWNSTREAM[stage]:
        status["stages"][downstream]["status"] = "stale"
        status["stages"][downstream]["confirmed_at"] = ""
        status["stages"][downstream]["updated_at"] = stamp
    save_status(status)
    return status


def artifact_path(stage: str) -> Path:
    validate_stage(stage)
    return active_workspace_dir() / STAGES[stage]


def backup_artifact(stage: str, source: Path | None = None) -> Path | None:
    validate_stage(stage)
    source = source or artifact_path(stage)
    if not source.exists():
        return None
    backup_dir = active_workspace_dir() / BACKUP_DIR
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / f"{stage}-{datetime.now().astimezone().strftime('%Y%m%d-%H%M%S')}{source.suffix}"
    shutil.copy2(source, backup)
    return backup
```

Modify `core/__init__.py` so `review` can be imported from `core`:

```python
try:
    from . import review
except Exception:
    review = None
```

Also add `"review"` to `__all__`.

- [ ] **Step 4: Run tests**

Run:

```bash
/Users/oliverchow/VideoLingo/.venv/bin/python -m unittest tests.test_review -v
```

Expected: both tests pass.

- [ ] **Step 5: Commit**

```bash
git add core/review.py core/__init__.py tests/test_review.py
git commit -m "feat: add review status core"
```

---

### Task 2: Add Artifact Save, Backup, and Invalidation Helpers

**Files:**
- Modify: `core/review.py`
- Modify: `tests/test_review.py`

- [ ] **Step 1: Write failing artifact tests**

Append these tests to `tests/test_review.py`:

```python
    def test_save_terminology_preserves_theme_and_invalidates_downstream(self):
        import json

        path = Path(self.job["path"]) / "output" / "log"
        path.mkdir(parents=True, exist_ok=True)
        terminology = path / "terminology.json"
        terminology.write_text(
            json.dumps(
                {
                    "theme": "Physics lecture",
                    "terms": [{"src": "force", "tgt": "力", "note": "physics"}],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        review.mark_confirmed("translation")

        review.save_terminology(
            [{"src": "energy", "tgt": "能量", "note": "physics"}],
            theme="Physics lecture",
        )

        saved = json.loads(terminology.read_text(encoding="utf-8"))
        self.assertEqual(saved["theme"], "Physics lecture")
        self.assertEqual(saved["terms"][0]["src"], "energy")
        status = review.load_status()
        self.assertEqual(status["stages"]["translation"]["status"], "stale")
        backups = list((Path(self.job["path"]) / "artifacts" / "reviews" / "backups").glob("terminology-*.json"))
        self.assertEqual(len(backups), 1)

    def test_save_table_creates_backup_and_validates_required_columns(self):
        import pandas as pd

        path = Path(self.job["path"]) / "output" / "log"
        path.mkdir(parents=True, exist_ok=True)
        artifact = path / "translation_results.xlsx"
        pd.DataFrame({"Source": ["hello"], "Translation": ["你好"]}).to_excel(artifact, index=False)

        review.save_table(
            "translation",
            pd.DataFrame({"Source": ["hello"], "Translation": ["您好"]}),
            required_columns=("Source", "Translation"),
        )

        saved = pd.read_excel(artifact)
        self.assertEqual(saved.at[0, "Translation"], "您好")
        backups = list((Path(self.job["path"]) / "artifacts" / "reviews" / "backups").glob("translation-*.xlsx"))
        self.assertEqual(len(backups), 1)

    def test_save_table_rejects_missing_required_columns(self):
        import pandas as pd

        with self.assertRaises(ValueError):
            review.save_table(
                "translation",
                pd.DataFrame({"Source": ["hello"]}),
                required_columns=("Source", "Translation"),
            )
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
/Users/oliverchow/VideoLingo/.venv/bin/python -m unittest tests.test_review -v
```

Expected: fail because `save_terminology` and `save_table` do not exist.

- [ ] **Step 3: Implement artifact helpers**

Add imports and functions to `core/review.py`:

```python
import json

import pandas as pd


def mark_saved(stage: str, status_value: str = "pending") -> dict[str, Any]:
    validate_stage(stage)
    status = load_status()
    status["stages"][stage]["status"] = status_value
    status["stages"][stage]["confirmed_at"] = ""
    status["stages"][stage]["updated_at"] = now_iso()
    save_status(status)
    return invalidate_downstream(stage, status)


def load_terminology() -> dict[str, Any]:
    path = artifact_path("terminology")
    if not path.exists():
        raise FileNotFoundError(path)
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
    data.setdefault("terms", [])
    return data


def save_terminology(terms: list[dict[str, Any]], theme: str | None = None) -> dict[str, Any]:
    path = artifact_path("terminology")
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if path.exists():
        with open(path, "r", encoding="utf-8") as file:
            existing = json.load(file) or {}
        backup_artifact("terminology", path)
    cleaned_terms = []
    for term in terms:
        cleaned_terms.append(
            {
                "src": str(term.get("src", "")).strip(),
                "tgt": str(term.get("tgt", "")).strip(),
                "note": str(term.get("note", "")).strip(),
            }
        )
    existing["terms"] = cleaned_terms
    if theme is not None:
        existing["theme"] = theme
    with open(path, "w", encoding="utf-8") as file:
        json.dump(existing, file, ensure_ascii=False, indent=4)
    mark_saved("terminology")
    return existing


def load_table(stage: str) -> pd.DataFrame:
    path = artifact_path(stage)
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_excel(path)


def validate_required_columns(df: pd.DataFrame, required_columns: tuple[str, ...]) -> None:
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")


def save_table(
    stage: str,
    df: pd.DataFrame,
    required_columns: tuple[str, ...],
    invalidate: bool = True,
) -> None:
    validate_stage(stage)
    validate_required_columns(df, required_columns)
    path = artifact_path(stage)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup_artifact(stage, path)
    df.to_excel(path, index=False)
    if invalidate:
        mark_saved(stage)
```

- [ ] **Step 4: Run tests**

Run:

```bash
/Users/oliverchow/VideoLingo/.venv/bin/python -m unittest tests.test_review -v
```

Expected: all review tests pass.

- [ ] **Step 5: Commit**

```bash
git add core/review.py tests/test_review.py
git commit -m "feat: add review artifact persistence"
```

---

### Task 3: Add Subtitle and TTS Review Helpers

**Files:**
- Modify: `core/review.py`
- Modify: `tests/test_review.py`

- [ ] **Step 1: Write failing tests for subtitle sync and TTS save**

Append these tests to `tests/test_review.py`:

```python
    def test_save_subtitles_updates_remerged_when_row_counts_match(self):
        import pandas as pd

        log_dir = Path(self.job["path"]) / "output" / "log"
        log_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"Source": ["A"], "Translation": ["甲"]}).to_excel(
            log_dir / "translation_results_for_subtitles.xlsx",
            index=False,
        )
        pd.DataFrame({"Source": ["A"], "Translation": ["甲"]}).to_excel(
            log_dir / "translation_results_remerged.xlsx",
            index=False,
        )

        review.save_subtitles(pd.DataFrame({"Source": ["A"], "Translation": ["乙"]}))

        display = pd.read_excel(log_dir / "translation_results_for_subtitles.xlsx")
        remerged = pd.read_excel(log_dir / "translation_results_remerged.xlsx")
        self.assertEqual(display.at[0, "Translation"], "乙")
        self.assertEqual(remerged.at[0, "Translation"], "乙")
        self.assertEqual(review.load_status()["stages"]["tts_text"]["status"], "stale")

    def test_save_subtitles_leaves_remerged_when_row_counts_differ(self):
        import pandas as pd

        log_dir = Path(self.job["path"]) / "output" / "log"
        log_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"Source": ["A"], "Translation": ["甲"]}).to_excel(
            log_dir / "translation_results_for_subtitles.xlsx",
            index=False,
        )
        pd.DataFrame({"Source": ["A", "B"], "Translation": ["甲", "乙"]}).to_excel(
            log_dir / "translation_results_remerged.xlsx",
            index=False,
        )

        review.save_subtitles(pd.DataFrame({"Source": ["A"], "Translation": ["丙"]}))

        remerged = pd.read_excel(log_dir / "translation_results_remerged.xlsx")
        self.assertEqual(len(remerged), 2)
        self.assertEqual(remerged.at[0, "Translation"], "甲")

    def test_save_tts_text_preserves_timing_columns(self):
        import pandas as pd

        audio_dir = Path(self.job["path"]) / "output" / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(
            {
                "number": [1],
                "start_time": ["00:00:00.000"],
                "end_time": ["00:00:02.000"],
                "duration": [2.0],
                "text": ["old"],
                "origin": ["source"],
            }
        ).to_excel(audio_dir / "tts_tasks.xlsx", index=False)

        review.save_table(
            "tts_text",
            pd.DataFrame(
                {
                    "number": [1],
                    "start_time": ["00:00:00.000"],
                    "end_time": ["00:00:02.000"],
                    "duration": [2.0],
                    "text": ["new"],
                    "origin": ["source"],
                }
            ),
            required_columns=("number", "start_time", "end_time", "duration", "text", "origin"),
        )

        saved = pd.read_excel(audio_dir / "tts_tasks.xlsx")
        self.assertEqual(saved.at[0, "text"], "new")
        self.assertEqual(saved.at[0, "duration"], 2.0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
/Users/oliverchow/VideoLingo/.venv/bin/python -m unittest tests.test_review -v
```

Expected: fail because `save_subtitles` does not exist.

- [ ] **Step 3: Implement subtitle save helper**

Add this to `core/review.py`:

```python
def save_subtitles(df: pd.DataFrame) -> None:
    validate_required_columns(df, ("Source", "Translation"))
    save_table("subtitles", df, required_columns=("Source", "Translation"), invalidate=False)

    remerged_path = active_workspace_dir() / "output/log/translation_results_remerged.xlsx"
    if remerged_path.exists():
        remerged = pd.read_excel(remerged_path)
        if len(remerged) == len(df) and {"Source", "Translation"}.issubset(remerged.columns):
            backup_dir = active_workspace_dir() / BACKUP_DIR
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup = backup_dir / f"subtitles-remerged-{datetime.now().astimezone().strftime('%Y%m%d-%H%M%S')}.xlsx"
            shutil.copy2(remerged_path, backup)
            remerged["Source"] = df["Source"]
            remerged["Translation"] = df["Translation"]
            remerged.to_excel(remerged_path, index=False)

    mark_saved("subtitles")
```

- [ ] **Step 4: Run tests**

Run:

```bash
/Users/oliverchow/VideoLingo/.venv/bin/python -m unittest tests.test_review -v
```

Expected: all review tests pass.

- [ ] **Step 5: Commit**

```bash
git add core/review.py tests/test_review.py
git commit -m "feat: add subtitle and tts review persistence"
```

---

### Task 4: Add Streamlit Review Workbench UI

**Files:**
- Create: `core/st_utils/review_section.py`
- Modify: `st.py`

- [ ] **Step 1: Create the review UI module**

Create `core/st_utils/review_section.py`:

```python
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
        if st.button(t("Mark as needs review"), key=f"review_pending_{stage}", width="stretch"):
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


def table_tab(stage: str, required_columns: tuple[str, ...], editable_columns: tuple[str, ...]) -> None:
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
            required_columns=("number", "start_time", "end_time", "duration", "text", "origin"),
            editable_columns=("text", "origin"),
        )
```

- [ ] **Step 2: Wire the section into `st.py`**

Add:

```python
from core.st_utils.review_section import review_section
```

Then call `review_section()` in `main()` after `download_video_section()` and before `text_processing_section()`.

- [ ] **Step 3: Compile to catch import errors**

Run:

```bash
/Users/oliverchow/VideoLingo/.venv/bin/python -m compileall -q core/st_utils/review_section.py st.py
```

Expected: exit 0.

- [ ] **Step 4: Commit**

```bash
git add core/st_utils/review_section.py st.py
git commit -m "feat: add Streamlit review workbench"
```

---

### Task 5: Add Review-Aware Pipeline Buttons

**Files:**
- Modify: `st.py`

- [ ] **Step 1: Add helper functions near `_get_text_steps()`**

Add this code to `st.py`:

```python
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
```

- [ ] **Step 2: Replace `_get_text_steps()` with review-aware groups**

Use this shape:

```python
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
```

- [ ] **Step 3: Replace text processing button logic**

Inside `text_processing_section()`, keep the existing completed-output branch. In the not-completed branch, show one action at a time:

```python
if runner.is_active or runner.is_done:
    _task_control_panel("_text_runner")
elif not _artifact_exists("terminology"):
    if st.button(t("Generate terminology for review"), key="generate_terms_button"):
        runner.start(_get_text_generation_steps())
        st.rerun()
elif not _stage_confirmed("terminology"):
    st.info(t("Review and confirm terminology before translation."))
elif not _artifact_exists("translation"):
    if st.button(t("Continue to translation"), key="continue_translation_button"):
        runner.start(_get_translation_steps())
        st.rerun()
elif not _stage_confirmed("translation"):
    st.info(t("Review and confirm translation before subtitle splitting."))
elif not _artifact_exists("subtitles"):
    if st.button(t("Generate subtitle split for review"), key="continue_subtitle_split_button"):
        runner.start(_get_subtitle_split_steps())
        st.rerun()
elif not _stage_confirmed("subtitles"):
    st.info(t("Review and confirm subtitles before final subtitle generation."))
else:
    if st.button(t("Generate final subtitles and video"), key="continue_subtitle_finalize_button"):
        runner.start(_get_subtitle_finalize_steps())
        st.rerun()
```

- [ ] **Step 4: Replace `_get_audio_steps()` with review-aware groups**

Use this shape:

```python
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
```

- [ ] **Step 5: Replace audio processing button logic**

Inside `audio_processing_section()`, keep the completed-output branch. In the not-completed branch:

```python
if runner.is_active or runner.is_done:
    _task_control_panel("_audio_runner")
elif not _artifact_exists("tts_text"):
    if st.button(t("Generate TTS text for review"), key="generate_tts_text_button"):
        runner.start(_get_tts_task_steps())
        st.rerun()
elif not _stage_confirmed("tts_text"):
    st.info(t("Review and confirm TTS text before dubbing."))
else:
    if st.button(t("Generate dubbing"), key="continue_audio_finalize_button"):
        runner.start(_get_audio_finalize_steps())
        st.rerun()
```

- [ ] **Step 6: Compile**

Run:

```bash
/Users/oliverchow/VideoLingo/.venv/bin/python -m compileall -q st.py
```

Expected: exit 0.

- [ ] **Step 7: Commit**

```bash
git add st.py
git commit -m "feat: add review-aware pipeline checkpoints"
```

---

### Task 6: Full Verification and Documentation

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add README documentation**

Add a short section after Task Workspaces:

```markdown
### Human Review Workbench

When a task workspace is active, VideoLingo shows a Review Workbench for terminology, translation, subtitle rows, and TTS text. Each review file belongs to the active workspace, and saving changes creates a backup under `artifacts/reviews/backups/`.

The app pauses at review checkpoints so you can confirm terminology before translation, translation before subtitle splitting, subtitles before SRT generation, and TTS text before dubbing.
```

- [ ] **Step 2: Run unit tests**

Run:

```bash
/Users/oliverchow/VideoLingo/.venv/bin/python -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 3: Compile changed modules**

Run:

```bash
/Users/oliverchow/VideoLingo/.venv/bin/python -m compileall -q core batch st.py
```

Expected: exit 0.

- [ ] **Step 4: Streamlit smoke test**

Run:

```bash
/Users/oliverchow/VideoLingo/.venv/bin/streamlit run st.py --server.headless=true --server.port=8765 --logger.level=error
```

Then request:

```bash
/Users/oliverchow/VideoLingo/.venv/bin/python - <<'PY'
import urllib.request
print(urllib.request.urlopen("http://localhost:8765", timeout=10).status)
PY
```

Expected: `200`. Stop the Streamlit process after the check.

- [ ] **Step 5: Commit documentation**

```bash
git add README.md
git commit -m "docs: document human review workbench"
```

- [ ] **Step 6: Final status check**

Run:

```bash
git status --short --branch
git log --oneline main..HEAD
```

Expected: working tree clean and review workbench commits present.

---

## Self-Review

Spec coverage:

- Terminology, translation, subtitle, and TTS text review are covered by Tasks 2, 3, and 4.
- Workspace-local status and backups are covered by Tasks 1 and 2.
- Downstream invalidation is covered by Tasks 2 and 3.
- Review-aware pipeline checkpoints are covered by Task 5.
- Documentation and verification are covered by Task 6.

Placeholder scan:

- No marker-only steps, fill-in instructions, or unspecified "add tests" steps.
- Every code-changing task includes concrete snippets and commands.

Type consistency:

- Stage names are consistently `terminology`, `translation`, `subtitles`, and `tts_text`.
- Required artifact columns match current pipeline files.
- Status values are consistently `pending`, `confirmed`, and `stale`.
