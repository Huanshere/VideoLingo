"""Local, single-user API. Start from the repository root with python api.py."""
from pathlib import Path
import shutil
from threading import Lock
from typing import Literal
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field

from core.pipeline import get_steps
from core.task_runner import TaskRunner
from core.utils.config_utils import load_key, update_key

app = FastAPI(title="VideoLingo", description="One operation at a time, using config.yaml and output/.")
runner = TaskRunner()
operation_lock = Lock()
OUTPUT = Path("output")


class InputRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: str = Field(min_length=1, description="Local file path or HTTP(S) video URL")
    existing: Literal["reject", "archive", "replace"] = "reject"


class RunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stage: Literal["subtitles", "dubbing", "all"] = "all"
    dubbing: bool = False
    target_language: str | None = Field(default=None, min_length=1)
    source_language: str | None = Field(default=None, min_length=1)


def require_idle():
    if runner.is_active:
        raise HTTPException(409, "An operation is active; wait for /status before continuing.")


def archive_output():
    from core.utils.onekeycleanup import cleanup
    cleanup()
    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        raise RuntimeError("Some output files could not be archived; inspect output/ before retrying.")


def prepare_input(source, existing):
    from core._1_ytdlp import (download_video_ytdlp, write_input_manifest,
                              sanitize_filename, GENERATED_AUDIO_NAMES, GENERATED_VIDEO_NAMES)
    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        if existing == "archive":
            archive_output()
        elif existing == "replace":
            shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(exist_ok=True)
    if urlparse(source).scheme in {"http", "https"}:
        download_video_ytdlp(source, resolution=load_key("ytb_resolution"))
    else:
        source = Path(source)
        name = sanitize_filename(source.stem) + source.suffix.lower()
        if name.lower() in GENERATED_AUDIO_NAMES | GENERATED_VIDEO_NAMES:
            name = "input_" + name
        destination = OUTPUT / name
        shutil.copy2(source, destination)
        kind = "video" if source.suffix.lower()[1:] in load_key("allowed_video_formats") else "audio"
        write_input_manifest(str(destination), kind)


@app.post("/input", status_code=202)
def set_input(request: InputRequest):
    """Prepare input in the background; poll /status before POST /run."""
    with operation_lock:
        require_idle()
        parsed = urlparse(request.source)
        if parsed.scheme in {"http", "https"}:
            if not parsed.netloc:
                raise HTTPException(422, "Invalid URL")
            source = request.source
        else:
            source = Path(request.source).resolve()
            if not source.is_file():
                raise HTTPException(422, "Source file does not exist")
            if source.is_relative_to(OUTPUT.resolve()):
                raise HTTPException(422, "Source must be outside output/; use /run for an existing input.")
            formats = load_key("allowed_video_formats") + load_key("allowed_audio_formats")
            if source.suffix.lower()[1:] not in formats:
                raise HTTPException(422, "Unsupported media format")
            source = str(source)
        if OUTPUT.exists() and any(OUTPUT.iterdir()) and request.existing == "reject":
            raise HTTPException(409, "output/ is not empty; explicitly choose archive or replace.")
        runner.start([("Prepare input", lambda: prepare_input(source, request.existing))])
        return {"accepted": True}


@app.post("/run", status_code=202)
def run(request: RunRequest):
    """Run or retry the shared pipeline. Parameters are saved to config.yaml."""
    with operation_lock:
        require_idle()
        from core._1_ytdlp import find_media_file
        try:
            _, kind = find_media_file()
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        needs_dubbing = request.stage == "dubbing" or (request.stage == "all" and request.dubbing)
        if needs_dubbing and kind == "audio":
            raise HTTPException(422, "Audio-only input supports subtitles, as in the UI.")
        if request.stage == "dubbing" and not all((OUTPUT / name).exists() for name in ("src.srt", "trans.srt")):
            raise HTTPException(409, "Generate subtitles before starting dubbing.")
        if request.target_language is not None:
            update_key("target_language", request.target_language)
        if request.source_language is not None:
            update_key("whisper.language", request.source_language)
        runner.start(get_steps(request.stage, request.dubbing))
        return {"accepted": True}


@app.get("/status")
def status():
    """In-memory execution state; output files survive server restarts."""
    files = sorted(p.name for p in OUTPUT.glob("*") if p.is_file() and not p.name.startswith('.'))
    return {
        "state": runner.state,
        "active": runner.is_active,
        "step": runner.current_label or None,
        "step_index": runner.current_step,
        "total_steps": runner.total_steps,
        "progress": runner.progress,
        "error": runner.error_msg or None,
        "files": files,
    }


@app.post("/stop")
def stop():
    """Cooperative stop: wait until active=false before another operation."""
    with operation_lock:
        runner.stop()
        return {"state": runner.state}


@app.get("/files/{name}")
def file(name: str):
    path = (OUTPUT / name).resolve()
    if path.parent != OUTPUT.resolve() or name.startswith('.') or not path.is_file():
        raise HTTPException(404, "Output file not found")
    return FileResponse(path, filename=path.name)


@app.post("/archive", status_code=202)
def archive():
    """Move output into history/ using the existing archive behavior."""
    with operation_lock:
        require_idle()
        if not OUTPUT.exists() or not any(OUTPUT.iterdir()):
            raise HTTPException(409, "No output to archive")
        runner.start([("Archive output", archive_output)])
        return {"accepted": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
