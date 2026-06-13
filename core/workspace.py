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
        "source": {
            "type": source_type,
            "path": source_path,
            "url": source_url,
        },
        "status": "created",
        "created_at": created_at,
        "updated_at": created_at,
        "current_stage": "",
        "error": "",
    }
    save_job(job_dir, job)
    save_config_snapshot(job_dir, config_path)
    return job


def save_config_snapshot(
    job_dir: str | os.PathLike[str],
    config_path: str | os.PathLike[str] = "config.yaml",
) -> None:
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


def list_jobs(
    workspace_root: str | os.PathLike[str] = DEFAULT_WORKSPACE_ROOT,
) -> list[dict[str, Any]]:
    root = Path(workspace_root)
    if not root.exists():
        return []

    jobs = []
    for child in sorted(root.iterdir(), reverse=True):
        if child.is_dir() and (child / JOB_FILE).is_file():
            jobs.append(load_job(child))
    return jobs
