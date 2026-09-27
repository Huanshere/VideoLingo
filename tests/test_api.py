"""Local API contract and shared execution; no models or network requests."""
from pathlib import Path
import subprocess
import sys
import threading
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest
import yaml

import api
from core import pipeline
from core.task_runner import TaskRunner, StopTask
from core.utils.decorator import except_handler


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.yaml").write_text(yaml.safe_dump({
        "allowed_video_formats": ["mp4"], "allowed_audio_formats": ["wav", "mp3"],
        "ytb_resolution": "360", "target_language": "English",
        "whisper": {"language": "auto", "detected_language": "en"},
    }), encoding="utf-8")
    monkeypatch.setattr(api, "runner", TaskRunner())
    with TestClient(api.app) as client:
        yield client
    api.runner.stop()
    if api.runner._thread:
        api.runner._thread.join(3)
        assert not api.runner._thread.is_alive()


def finish(client):
    api.runner._thread.join(3)
    assert not api.runner._thread.is_alive()
    return client.get("/status").json()


def input_file(client, filename="sample.mp4", **options):
    Path(filename).write_bytes(b"test media")
    response = client.post("/input", json={"source": str(Path(filename).resolve()), **options})
    assert response.status_code == 202, response.text
    assert finish(client)["state"] == "completed"


def test_input_requires_explicit_replacement_and_validates_before_deleting(client):
    input_file(client)
    assert Path("output/sample.mp4").read_bytes() == b"test media"
    Path("output/trans.srt").write_text("keep")
    assert client.post("/input", json={"source": str(Path("sample.mp4").resolve())}).status_code == 409
    assert client.post("/input", json={"source": "missing.mp4", "existing": "replace"}).status_code == 422
    assert Path("output/trans.srt").exists()
    assert client.post("/input", json={"source": "output/sample.mp4", "existing": "replace"}).status_code == 422
    input_file(client, existing="replace")
    assert not Path("output/trans.srt").exists()


def test_archive_moves_markers_and_allows_next_input(client):
    input_file(client)
    Path("output/.subtitle_done").touch()
    Path("output/trans.srt").write_text("subtitle")
    assert client.post("/archive").status_code == 202
    assert finish(client)["state"] == "completed"
    assert Path("history/sample/.subtitle_done").exists()
    assert not list(Path("output").glob("*"))
    input_file(client, "next.mp4")


def test_url_uses_existing_downloader(client, monkeypatch):
    from core import _1_ytdlp
    calls = []
    monkeypatch.setattr(_1_ytdlp, "download_video_ytdlp", lambda source, **kwargs: calls.append((source, kwargs)))
    assert client.post("/input", json={"source": "https://example.com/video"}).status_code == 202
    assert finish(client)["state"] == "completed"
    assert calls == [("https://example.com/video", {"resolution": "360"})]


def test_run_uses_shared_plan_and_saves_parameters(client, monkeypatch):
    input_file(client)
    calls = []
    def plan(stage, dubbing):
        calls.append((stage, dubbing))
        return [("Translate", lambda: Path("output/trans.srt").write_text("translated"))]
    monkeypatch.setattr(api, "get_steps", plan)
    response = client.post("/run", json={"stage": "all", "dubbing": True, "target_language": "zh", "source_language": "ja"})
    assert response.status_code == 202
    state = finish(client)
    assert calls == [("all", True)]
    assert state["state"] == "completed" and state["progress"] == 1
    assert "trans.srt" in state["files"]
    config = yaml.safe_load(Path("config.yaml").read_text())
    assert config["target_language"] == "zh"
    assert config["whisper"]["detected_language"] == "ja"
    assert client.get("/files/trans.srt").text == "translated"
    assert client.get("/files/..%5Cconfig.yaml").status_code == 404


def test_busy_and_stopping_reject_mutations(client, monkeypatch):
    input_file(client)
    entered, release = threading.Event(), threading.Event()
    def work():
        entered.set()
        assert release.wait(3)
    monkeypatch.setattr(api, "get_steps", lambda *args: [("Slow step", work)])
    try:
        assert client.post("/run", json={}).status_code == 202
        assert entered.wait(1)
        for route, body in (("/run", {"target_language": "changed"}), ("/input", {"source": "sample.mp4", "existing": "replace"}), ("/archive", {})):
            assert client.post(route, json=body).status_code == 409
        assert client.post("/stop").json()["state"] == "stopping"
        assert client.get("/status").json()["active"]
        assert client.post("/run", json={}).status_code == 409
        assert yaml.safe_load(Path("config.yaml").read_text())["target_language"] == "English"
    finally:
        release.set()
    assert finish(client)["state"] == "stopped"


def test_failure_reports_step_and_can_retry(client, monkeypatch):
    input_file(client)
    def fail():
        raise RuntimeError("synthetic failure")
    monkeypatch.setattr(api, "get_steps", lambda *args: [("Translate", fail)])
    assert client.post("/run", json={}).status_code == 202
    state = finish(client)
    assert state["state"] == "error" and state["step"] == "Translate"
    assert state["error"] == "synthetic failure"
    monkeypatch.setattr(api, "get_steps", lambda *args: [("Translate", lambda: None)])
    assert client.post("/run", json={}).status_code == 202
    assert finish(client)["state"] == "completed"


def test_preconditions_and_schema(client):
    assert client.post("/run", json={}).status_code == 409
    assert client.post("/run", json={"stage": "unknown"}).status_code == 422
    assert client.post("/run", json={"typo": True}).status_code == 422
    input_file(client, "sample.wav")
    assert client.post("/run", json={"stage": "all", "dubbing": True}).status_code == 422
    assert "/run" in client.get("/openapi.json").json()["paths"]


def test_dubbing_requires_subtitles(client):
    input_file(client)
    assert client.post("/run", json={"stage": "dubbing"}).status_code == 409


def test_shared_pipeline_order_and_done_markers(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    calls = []
    def module(name):
        return SimpleNamespace(**{call.split('.')[1]: lambda call=call: calls.append(call)
            for _, group in pipeline.SUBTITLE_STEPS + pipeline.DUBBING_STEPS
            for call in group if name == "core." + call.split('.')[0]})
    monkeypatch.setattr(pipeline, "import_module", module)
    for _, step in pipeline.get_steps("all", dubbing=True):
        step()
    expected = [call for _, group in pipeline.SUBTITLE_STEPS + pipeline.DUBBING_STEPS for call in group]
    assert calls == expected
    assert Path("output/.subtitle_done").exists()
    assert Path("output/.dubbing_done").exists()
    monkeypatch.setattr(pipeline, "import_module", lambda _: (_ for _ in ()).throw(RuntimeError("failed")))
    with pytest.raises(RuntimeError):
        pipeline.get_steps("subtitles")[0][1]()
    assert not Path("output/.subtitle_done").exists()


def test_pause_stop_and_no_following_steps():
    runner = TaskRunner()
    entered, release = threading.Event(), threading.Event()
    calls = []
    def work():
        entered.set()
        assert release.wait(3)
    try:
        runner.start([("one", work), ("two", lambda: calls.append("two"))])
        assert entered.wait(1)
        runner.pause()
        assert runner.state == "paused"
        runner.stop()
        with pytest.raises(RuntimeError):
            runner.start([])
    finally:
        release.set()
        runner._thread.join(3)
    assert runner.state == "stopped" and not runner.is_active
    assert calls == []


def test_cancellation_is_not_retried():
    calls = []
    @except_handler("test", retry=3, delay=0)
    def cancel():
        calls.append(1)
        raise StopTask()
    with pytest.raises(StopTask):
        cancel()
    assert calls == [1]


def test_serial_inputs_keep_distinct_archives(client):
    input_file(client, "first.mp4")
    input_file(client, "second.mp4", existing="archive")
    assert Path("history/first/first.mp4").exists()
    assert Path("output/second.mp4").exists()
    assert client.post("/archive").status_code == 202
    assert finish(client)["state"] == "completed"
    assert Path("history/first/first.mp4").exists()
    assert Path("history/second/second.mp4").exists()


def test_api_import_does_not_load_ui_or_models():
    result = subprocess.run([
        sys.executable, "-c",
        "import api, sys; assert not {'streamlit', 'torch', 'spacy', 'qwen_asr'} & sys.modules.keys()",
    ], cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_transcribe_stage_and_resume(client, monkeypatch):
    input_file(client)
    assert client.post("/resume").status_code == 409
    calls = []
    def plan(stage, dubbing):
        calls.append(stage)
        return [("Checkpoint", lambda: (api.runner.pause("Review"), TaskRunner.check_cancel()))]
    monkeypatch.setattr(api, "get_steps", plan)
    assert client.post("/run", json={"stage": "transcribe"}).status_code == 202
    for _ in range(300):
        if client.get("/status").json()["state"] == "paused":
            break
        threading.Event().wait(0.01)
    assert client.get("/status").json()["pause_message"] == "Review"
    assert client.post("/resume").json()["state"] == "running"
    state = finish(client)
    assert calls == ["transcribe"]
    assert state["state"] == "completed" and state["pause_message"] is None
