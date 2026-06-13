# Task Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add isolated task workspaces so Streamlit and batch runs can write artifacts under `workspace/jobs/<job_id>/` while legacy `output/` runs keep working.

**Architecture:** Add `core/workspace.py` as the single workspace boundary. Existing pipeline code gets workspace-aware paths through `core/utils/models.py` and small call-site updates for hardcoded `output/` paths. Streamlit owns active job selection through session state and the workspace module mirrors it into an environment variable so pipeline functions can resolve paths without threading a job object through every step.

**Tech Stack:** Python 3.10, ruamel.yaml, Streamlit session state, unittest, existing VideoLingo pipeline modules.

---

## File Structure

- Create `core/workspace.py`: workspace metadata, active workspace state, path resolution, config snapshots.
- Modify `core/utils/models.py`: replace static output strings with dynamic workspace-aware path objects.
- Modify `core/_1_ytdlp.py`: use workspace output paths for downloads and video discovery.
- Modify `core/st_utils/download_video_section.py`: upload/delete files in the active workspace output directory.
- Modify `core/st_utils/imports_and_utils.py`: zip SRT files from active workspace output.
- Modify `core/utils/onekeycleanup.py`: archive active workspace output into workspace artifacts/history.
- Modify `core/utils/delete_retry_dubbing.py`: delete dubbing files from active workspace output.
- Modify `st.py`: add task selector UI and activate selected workspace before pipeline actions.
- Modify `batch/utils/batch_processor.py`: create or reuse one workspace per batch row and snapshot row config.
- Modify `batch/utils/video_processor.py`: process each video inside the active workspace output directory.
- Create `tests/test_workspace.py`: focused workspace unit tests.

---

### Task 1: Workspace Core

**Files:**
- Create: `core/workspace.py`
- Test: `tests/test_workspace.py`

- [ ] **Step 1: Write failing workspace creation tests**

Create `tests/test_workspace.py` with tests that use temporary roots and config files:

```python
import os
import tempfile
import unittest
from pathlib import Path

from ruamel.yaml import YAML

from core import workspace


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config_path = self.root / "config.yaml"
        self.config_path.write_text("display_language: en\napi:\n  key: ''\n", encoding="utf-8")
        workspace.clear_active_workspace()

    def tearDown(self):
        workspace.clear_active_workspace()

    def test_create_job_writes_metadata_and_config_snapshot(self):
        job = workspace.create_job(
            name="My Video!",
            source_type="upload",
            source_path="input.mp4",
            workspace_root=self.root / "jobs",
            config_path=self.config_path,
        )

        self.assertTrue(Path(job["path"]).is_dir())
        self.assertTrue((Path(job["path"]) / "output").is_dir())
        self.assertTrue((Path(job["path"]) / "job.yaml").is_file())
        self.assertTrue((Path(job["path"]) / "config.snapshot.yaml").is_file())
        self.assertEqual(job["name"], "My Video!")
        self.assertEqual(job["source"]["type"], "upload")

    def test_active_workspace_resolves_output_path(self):
        job = workspace.create_job(
            name="Video",
            workspace_root=self.root / "jobs",
            config_path=self.config_path,
        )
        workspace.set_active_workspace(job["path"])

        resolved = workspace.output_path("log", "file.txt")

        self.assertEqual(
            os.fspath(resolved),
            str(Path(job["path"]) / "output" / "log" / "file.txt"),
        )

    def test_legacy_output_path_without_active_workspace(self):
        workspace.clear_active_workspace()

        self.assertEqual(os.fspath(workspace.output_path("log", "file.txt")), "output/log/file.txt")

    def test_archive_job_marks_status_without_deleting_files(self):
        job = workspace.create_job(
            name="Video",
            workspace_root=self.root / "jobs",
            config_path=self.config_path,
        )

        workspace.archive_job(job["path"])
        loaded = workspace.load_job(job["path"])

        self.assertEqual(loaded["status"], "archived")
        self.assertTrue(Path(job["path"]).exists())

    def test_config_snapshot_is_independent_from_global_config(self):
        job = workspace.create_job(
            name="Video",
            workspace_root=self.root / "jobs",
            config_path=self.config_path,
        )
        self.config_path.write_text("display_language: zh-CN\napi:\n  key: changed\n", encoding="utf-8")

        yaml = YAML()
        snapshot = yaml.load((Path(job["path"]) / "config.snapshot.yaml").read_text(encoding="utf-8"))

        self.assertEqual(snapshot["display_language"], "en")
        self.assertEqual(snapshot["api"]["key"], "")
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
/Users/oliverchow/VideoLingo/.venv/bin/python -m unittest tests.test_workspace -v
```

Expected: FAIL because `core.workspace` does not exist.

- [ ] **Step 3: Implement `core/workspace.py`**

Add:

```python
from __future__ import annotations

import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

ACTIVE_WORKSPACE_ENV = "VIDEOLINGO_ACTIVE_WORKSPACE"
DEFAULT_WORKSPACE_ROOT = Path("workspace") / "jobs"
JOB_FILE = "job.yaml"
CONFIG_SNAPSHOT_FILE = "config.snapshot.yaml"

yaml = YAML()
yaml.preserve_quotes = True


class WorkspacePath:
    def __init__(self, relative_path: str):
        self.relative_path = relative_path.replace("\\", "/").strip("/")

    def resolve(self) -> str:
        return resolve_path(self.relative_path)

    def __fspath__(self) -> str:
        return self.resolve()

    def __str__(self) -> str:
        return self.resolve()

    def __repr__(self) -> str:
        return repr(self.resolve())


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._")
    return slug[:60] or "task"


def get_active_workspace() -> str | None:
    value = os.environ.get(ACTIVE_WORKSPACE_ENV, "").strip()
    return value or None


def set_active_workspace(path: str | os.PathLike[str]) -> str:
    job_dir = Path(path)
    if not (job_dir / JOB_FILE).is_file():
        raise FileNotFoundError(f"Workspace metadata not found: {job_dir / JOB_FILE}")
    os.environ[ACTIVE_WORKSPACE_ENV] = str(job_dir)
    return str(job_dir)


def clear_active_workspace() -> None:
    os.environ.pop(ACTIVE_WORKSPACE_ENV, None)


def workspace_path(relative_path: str) -> WorkspacePath:
    return WorkspacePath(relative_path)


def output_path(*parts: str) -> WorkspacePath:
    clean = [part.strip("/\\") for part in parts if part]
    return workspace_path("/".join(["output", *clean]))


def resolve_path(relative_path: str) -> str:
    active = get_active_workspace()
    if active:
        return str(Path(active) / relative_path)
    return relative_path


def create_job(
    name: str | None = None,
    source_type: str = "",
    source_path: str = "",
    source_url: str = "",
    workspace_root: str | os.PathLike[str] = DEFAULT_WORKSPACE_ROOT,
    config_path: str | os.PathLike[str] = "config.yaml",
) -> dict[str, Any]:
    title = name or "Untitled Task"
    timestamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    job_id = f"{timestamp}-{_slugify(title)}"
    job_dir = Path(workspace_root) / job_id
    suffix = 2
    while job_dir.exists():
        job_dir = Path(workspace_root) / f"{job_id}-{suffix}"
        suffix += 1

    (job_dir / "output").mkdir(parents=True, exist_ok=False)
    (job_dir / "logs").mkdir(parents=True, exist_ok=True)
    (job_dir / "artifacts").mkdir(parents=True, exist_ok=True)

    created_at = _now()
    job = {
        "id": job_dir.name,
        "name": title,
        "path": str(job_dir),
        "source": {"type": source_type, "path": source_path, "url": source_url},
        "status": "created",
        "created_at": created_at,
        "updated_at": created_at,
        "current_stage": "",
        "error": "",
    }
    save_job(job_dir, job)
    save_config_snapshot(job_dir, config_path)
    return job


def save_config_snapshot(job_dir: str | os.PathLike[str], config_path: str | os.PathLike[str] = "config.yaml") -> None:
    src = Path(config_path)
    dst = Path(job_dir) / CONFIG_SNAPSHOT_FILE
    if src.exists():
        shutil.copy2(src, dst)
    else:
        dst.write_text("{}\n", encoding="utf-8")


def load_job(job_dir: str | os.PathLike[str]) -> dict[str, Any]:
    with open(Path(job_dir) / JOB_FILE, "r", encoding="utf-8") as file:
        data = yaml.load(file) or {}
    data["path"] = str(Path(job_dir))
    return data


def save_job(job_dir: str | os.PathLike[str], data: dict[str, Any]) -> None:
    data = dict(data)
    data["path"] = str(Path(job_dir))
    data["updated_at"] = data.get("updated_at") or _now()
    with open(Path(job_dir) / JOB_FILE, "w", encoding="utf-8") as file:
        yaml.dump(data, file)


def update_job(job_dir: str | os.PathLike[str], **updates: Any) -> dict[str, Any]:
    job = load_job(job_dir)
    job.update(updates)
    job["updated_at"] = _now()
    save_job(job_dir, job)
    return job


def archive_job(job_dir: str | os.PathLike[str]) -> dict[str, Any]:
    return update_job(job_dir, status="archived")


def list_jobs(workspace_root: str | os.PathLike[str] = DEFAULT_WORKSPACE_ROOT) -> list[dict[str, Any]]:
    root = Path(workspace_root)
    if not root.exists():
        return []
    jobs = []
    for child in sorted(root.iterdir(), reverse=True):
        if child.is_dir() and (child / JOB_FILE).is_file():
            jobs.append(load_job(child))
    return jobs
```

- [ ] **Step 4: Run workspace tests**

Run:

```bash
/Users/oliverchow/VideoLingo/.venv/bin/python -m unittest tests.test_workspace -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add core/workspace.py tests/test_workspace.py
git commit -m "feat: add task workspace core"
```

---

### Task 2: Workspace-Aware Output Constants

**Files:**
- Modify: `core/utils/models.py`
- Modify: `core/_10_gen_audio.py`
- Modify: `core/_11_merge_audio.py`
- Test: `tests/test_workspace.py`

- [ ] **Step 1: Add a test for dynamic model paths**

Append to `tests/test_workspace.py`:

```python
    def test_model_constants_resolve_against_active_workspace(self):
        from core.utils import models

        job = workspace.create_job(
            name="Video",
            workspace_root=self.root / "jobs",
            config_path=self.config_path,
        )
        workspace.set_active_workspace(job["path"])

        self.assertEqual(
            os.fspath(models._2_CLEANED_CHUNKS),
            str(Path(job["path"]) / "output" / "log" / "cleaned_chunks.xlsx"),
        )
        self.assertEqual(str(models._AUDIO_TMP_DIR), str(Path(job["path"]) / "output" / "audio" / "tmp"))
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
/Users/oliverchow/VideoLingo/.venv/bin/python -m unittest tests.test_workspace.WorkspaceTests.test_model_constants_resolve_against_active_workspace -v
```

Expected: FAIL because constants are static strings.

- [ ] **Step 3: Update `core/utils/models.py`**

Replace static strings with:

```python
from core.workspace import workspace_path

_2_CLEANED_CHUNKS = workspace_path("output/log/cleaned_chunks.xlsx")
_3_1_SPLIT_BY_NLP = workspace_path("output/log/split_by_nlp.txt")
_3_2_SPLIT_BY_MEANING = workspace_path("output/log/split_by_meaning.txt")
_4_1_TERMINOLOGY = workspace_path("output/log/terminology.json")
_4_2_TRANSLATION = workspace_path("output/log/translation_results.xlsx")
_5_SPLIT_SUB = workspace_path("output/log/translation_results_for_subtitles.xlsx")
_5_REMERGED = workspace_path("output/log/translation_results_remerged.xlsx")
_8_1_AUDIO_TASK = workspace_path("output/audio/tts_tasks.xlsx")

_OUTPUT_DIR = workspace_path("output")
_AUDIO_DIR = workspace_path("output/audio")
_RAW_AUDIO_FILE = workspace_path("output/audio/raw.mp3")
_VOCAL_AUDIO_FILE = workspace_path("output/audio/vocal.mp3")
_BACKGROUND_AUDIO_FILE = workspace_path("output/audio/background.mp3")
_AUDIO_REFERS_DIR = workspace_path("output/audio/refers")
_AUDIO_SEGS_DIR = workspace_path("output/audio/segs")
_AUDIO_TMP_DIR = workspace_path("output/audio/tmp")
```

Keep the existing `__all__` list unchanged.

- [ ] **Step 4: Replace import-time audio templates**

In `core/_10_gen_audio.py`, replace global `TEMP_FILE_TEMPLATE` and `OUTPUT_FILE_TEMPLATE` with helper functions:

```python
def temp_file_path(number, line_index):
    return os.path.join(str(_AUDIO_TMP_DIR), f"{number}_{line_index}_temp.wav")


def output_file_path(number, line_index):
    return os.path.join(str(_AUDIO_SEGS_DIR), f"{number}_{line_index}.wav")
```

Use those helpers in `process_row()` and `merge_chunks()`.

In `core/_11_merge_audio.py`, replace `OUTPUT_FILE_TEMPLATE` with:

```python
def output_file_path(number, line_index):
    return os.path.join(str(_AUDIO_SEGS_DIR), f"{number}_{line_index}.wav")
```

Use it in `get_audio_files()`.

- [ ] **Step 5: Run tests**

Run:

```bash
/Users/oliverchow/VideoLingo/.venv/bin/python -m unittest tests.test_workspace -v
/Users/oliverchow/VideoLingo/.venv/bin/python -m compileall -q core
```

Expected: PASS and no compile errors.

- [ ] **Step 6: Commit**

```bash
git add core/utils/models.py core/_10_gen_audio.py core/_11_merge_audio.py tests/test_workspace.py
git commit -m "feat: resolve pipeline paths through active workspace"
```

---

### Task 3: Streamlit Workspace Selector And Output Helpers

**Files:**
- Modify: `st.py`
- Modify: `core/_1_ytdlp.py`
- Modify: `core/st_utils/download_video_section.py`
- Modify: `core/st_utils/imports_and_utils.py`
- Modify: `core/utils/onekeycleanup.py`
- Modify: `core/utils/delete_retry_dubbing.py`
- Test: `tests/test_workspace.py`

- [ ] **Step 1: Add tests for active output helpers**

Append:

```python
    def test_find_video_files_uses_active_workspace_output(self):
        from core._1_ytdlp import find_video_files

        job = workspace.create_job(
            name="Video",
            workspace_root=self.root / "jobs",
            config_path=self.config_path,
        )
        output_dir = Path(job["path"]) / "output"
        (output_dir / "sample.mp4").write_bytes(b"video")
        workspace.set_active_workspace(job["path"])

        self.assertEqual(find_video_files(), str(output_dir / "sample.mp4"))
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
/Users/oliverchow/VideoLingo/.venv/bin/python -m unittest tests.test_workspace.WorkspaceTests.test_find_video_files_uses_active_workspace_output -v
```

Expected: FAIL because `find_video_files()` scans legacy `output/`.

- [ ] **Step 3: Update `core/_1_ytdlp.py`**

Import workspace helpers:

```python
from core.workspace import output_path
```

Change defaults:

```python
def download_video_ytdlp(url, save_path=None, resolution='1080'):
    save_path = str(save_path or output_path())
```

```python
def find_video_files(save_path=None):
    save_path = str(save_path or output_path())
```

Update the generated-output filter to use the resolved output path:

```python
generated_prefix = os.path.join(save_path, "output")
video_files = [file for file in video_files if not os.path.basename(file).startswith("output")]
```

- [ ] **Step 4: Update upload/download UI paths**

In `core/st_utils/download_video_section.py`, import `output_path` and replace `OUTPUT_DIR` usage with `str(output_path())` inside functions. `convert_audio_to_video()` should compute `output_dir = str(output_path())`.

In `core/st_utils/imports_and_utils.py`, use `str(output_path())` for the subtitle zip source.

In `core/utils/delete_retry_dubbing.py`, use `output_path()` for `dub.wav`, `output_dub.mp4`, and `audio/segs`.

In `core/utils/onekeycleanup.py`, use `str(output_path())` as the source output directory and move files into `artifacts/history/<video_name>` inside the active workspace when one is active. Keep `history/` as the legacy fallback.

- [ ] **Step 5: Add Streamlit selector**

In `st.py`, import:

```python
from core import workspace
```

Add helper:

```python
def workspace_section():
    st.sidebar.header(t("Task Workspace"))
    jobs = workspace.list_jobs()
    labels = [f"{job['name']} · {job['status']} · {job['id']}" for job in jobs]
    selected = st.sidebar.selectbox(t("Continue task"), [""] + labels)
    if selected:
        job = jobs[labels.index(selected)]
        workspace.set_active_workspace(job["path"])
        st.session_state["_active_workspace"] = job["path"]
    elif st.session_state.get("_active_workspace"):
        workspace.set_active_workspace(st.session_state["_active_workspace"])

    new_name = st.sidebar.text_input(t("New task name"), value="")
    if st.sidebar.button(t("New task"), key="new_workspace_task"):
        job = workspace.create_job(name=new_name or "VideoLingo Task")
        workspace.set_active_workspace(job["path"])
        st.session_state["_active_workspace"] = job["path"]
        st.rerun()

    active = workspace.get_active_workspace()
    if active:
        job = workspace.load_job(active)
        st.sidebar.caption(f"{job['name']} · {job['status']}")
        if st.sidebar.button(t("Archive task"), key="archive_workspace_task"):
            workspace.archive_job(active)
            workspace.clear_active_workspace()
            st.session_state.pop("_active_workspace", None)
            st.rerun()
```

Call `workspace_section()` before `page_setting()` in the sidebar. Change `SUB_VIDEO` and `DUB_VIDEO` to calls inside functions:

```python
sub_video = str(workspace.output_path("output_sub.mp4"))
dub_video = str(workspace.output_path("output_dub.mp4"))
```

- [ ] **Step 6: Run tests and compile**

Run:

```bash
/Users/oliverchow/VideoLingo/.venv/bin/python -m unittest tests.test_workspace -v
/Users/oliverchow/VideoLingo/.venv/bin/python -m compileall -q core st.py
```

Expected: PASS and no compile errors.

- [ ] **Step 7: Commit**

```bash
git add st.py core/_1_ytdlp.py core/st_utils/download_video_section.py core/st_utils/imports_and_utils.py core/utils/onekeycleanup.py core/utils/delete_retry_dubbing.py tests/test_workspace.py
git commit -m "feat: add Streamlit task workspace selection"
```

---

### Task 4: Batch Workspace Isolation

**Files:**
- Modify: `batch/utils/batch_processor.py`
- Modify: `batch/utils/video_processor.py`
- Test: `tests/test_workspace.py`

- [ ] **Step 1: Add batch workspace tests**

Append:

```python
    def test_batch_workspace_path_can_be_stored_per_row(self):
        import pandas as pd
        from batch.utils.batch_processor import ensure_workspace_columns

        df = pd.DataFrame({"Video File": ["a.mp4"], "Status": [None]})
        updated = ensure_workspace_columns(df)

        self.assertIn("Workspace", updated.columns)
        self.assertEqual(updated.at[0, "Workspace"], "")
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
/Users/oliverchow/VideoLingo/.venv/bin/python -m unittest tests.test_workspace.WorkspaceTests.test_batch_workspace_path_can_be_stored_per_row -v
```

Expected: FAIL because `ensure_workspace_columns` does not exist.

- [ ] **Step 3: Update batch processor**

Add to `batch/utils/batch_processor.py`:

```python
from core import workspace


def ensure_workspace_columns(df):
    if "Workspace" not in df.columns:
        df["Workspace"] = ""
    return df


def get_or_create_batch_workspace(row, index):
    current = row.get("Workspace", "")
    if isinstance(current, str) and current and os.path.exists(current):
        return current
    video_file = str(row["Video File"])
    job = workspace.create_job(
        name=os.path.splitext(os.path.basename(video_file))[0] or f"Batch Task {index + 1}",
        source_type="batch",
        source_path=video_file if not video_file.startswith("http") else "",
        source_url=video_file if video_file.startswith("http") else "",
    )
    return job["path"]
```

In `process_batch()`, call `ensure_workspace_columns(df)` after reading Excel. Before `process_video`, set active workspace:

```python
workspace_path = get_or_create_batch_workspace(row, index)
df.at[index, "Workspace"] = workspace_path
workspace.set_active_workspace(workspace_path)
```

Clear active workspace after each row in `finally`.

- [ ] **Step 4: Update video processor**

In `batch/utils/video_processor.py`, import `output_path`. Replace `OUTPUT_DIR = 'output'` usage in `prepare_output_folder()` and `process_input_file()` with `str(output_path())`.

Remove restore-from-`batch/output/ERROR` behavior from `batch_processor.py` for workspace-aware retries. Failed work remains in its own workspace.

- [ ] **Step 5: Run tests and compile**

Run:

```bash
/Users/oliverchow/VideoLingo/.venv/bin/python -m unittest tests.test_workspace -v
/Users/oliverchow/VideoLingo/.venv/bin/python -m compileall -q batch core
```

Expected: PASS and no compile errors.

- [ ] **Step 6: Commit**

```bash
git add batch/utils/batch_processor.py batch/utils/video_processor.py tests/test_workspace.py
git commit -m "feat: isolate batch tasks in workspaces"
```

---

### Task 5: Final Verification And Docs Note

**Files:**
- Modify: `README.md` or `docs/pages/docs/start.en-US.md`

- [ ] **Step 1: Add a short user-facing note**

Add a short note near the quick start docs:

```markdown
### Task Workspaces

VideoLingo stores each new task under `workspace/jobs/<job_id>/` when launched from the Streamlit task selector. Each workspace contains a config snapshot and its own `output/` folder, so separate videos do not overwrite each other's intermediate files.
```

- [ ] **Step 2: Run full lightweight verification**

Run:

```bash
/Users/oliverchow/VideoLingo/.venv/bin/python -m unittest discover -s tests -v
/Users/oliverchow/VideoLingo/.venv/bin/python -m compileall -q core batch st.py
git status --short
```

Expected: tests pass, compile succeeds, status shows only intended files.

- [ ] **Step 3: Commit**

```bash
git add README.md docs/pages/docs/start.en-US.md
git commit -m "docs: document task workspace behavior"
```

---

## Self-Review

Spec coverage:

- Workspace creation, metadata, config snapshots: Task 1.
- Workspace-aware output paths and legacy fallback: Task 1 and Task 2.
- Streamlit new/continue/archive task UI: Task 3.
- Batch per-video workspace isolation: Task 4.
- Testing: Tasks 1 through 5.

Scope check:

- The plan does not add SQLite, multi-user execution, human review pages, cost tracking, or provider health dashboards.
- The plan keeps migration incremental and compatible with legacy `output/`.

Placeholder scan:

- No placeholder markers or vague future task markers are intentionally left in this plan.
