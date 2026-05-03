from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
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


def invalidate_downstream(
    stage: str, status: dict[str, Any] | None = None
) -> dict[str, Any]:
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
    backup = (
        backup_dir
        / f"{stage}-{datetime.now().astimezone().strftime('%Y%m%d-%H%M%S')}{source.suffix}"
    )
    shutil.copy2(source, backup)
    return backup


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


def save_terminology(
    terms: list[dict[str, Any]], theme: str | None = None
) -> dict[str, Any]:
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


def validate_required_columns(
    df: pd.DataFrame, required_columns: tuple[str, ...]
) -> None:
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
