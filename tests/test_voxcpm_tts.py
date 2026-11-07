import base64
import io
import json
import wave
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from core.tts_backend import voxcpm_tts as voxcpm


@pytest.fixture(autouse=True)
def isolate_manual_reference(tmp_path, monkeypatch):
    monkeypatch.setattr(
        voxcpm, "MANUAL_REFERENCE_AUDIO_PATH", tmp_path / "runtime" / "voxcpm" / "reference.wav"
    )


def _event(event_type, **payload):
    return f"data: {json.dumps({'type': event_type, **payload})}"


def _sse_lines(*events):
    lines = []
    for event in events:
        lines.extend([event, ""])
    return lines


def _wav_bytes():
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"\x00\x00" * 160)
    return buffer.getvalue()


def _streamed_wav_bytes():
    wav = bytearray(_wav_bytes())
    wav[4:8] = b"\xff\xff\xff\xff"
    wav[40:44] = b"\xff\xff\xff\xff"
    return bytes(wav)


def test_finalize_streamed_wav_repairs_unknown_lengths():
    normalized = voxcpm._finalize_streamed_wav(_streamed_wav_bytes())
    with wave.open(io.BytesIO(normalized), "rb") as wav:
        assert wav.getnchannels() == 1
        assert wav.getframerate() == 16000
        assert wav.getnframes() == 160


def test_uploaded_reference_audio_is_normalized_and_saved():
    output = voxcpm.save_voxcpm_reference_audio(_wav_bytes())
    assert output == voxcpm.MANUAL_REFERENCE_AUDIO_PATH
    with wave.open(str(output), "rb") as wav:
        assert wav.getnchannels() == 1
        assert wav.getframerate() == 16000
        assert wav.getnframes() > 0


def test_voxcpm_assembles_sse_wav_without_reference_audio(tmp_path):
    response = SimpleNamespace(
        status_code=200,
        iter_lines=lambda decode_unicode: _sse_lines(
            _event("speech.audio.delta", audio=base64.b64encode(_streamed_wav_bytes()).decode()),
            _event("speech.audio.done"),
        ),
        close=Mock(),
    )
    output = tmp_path / "speech.wav"
    settings = {
        "api_key": "test-key",
        "model_id": "VoxCPM2",
        "base_url": "https://api.modelbest.cn/v1/",
        "mode": "default",
    }
    with patch.object(voxcpm, "load_key_or", return_value=settings), patch.object(
        voxcpm.requests, "post", return_value=response
    ) as post:
        assert voxcpm.voxcpm_tts_for_videolingo("Hello", str(output), 1, None)

    with wave.open(str(output), "rb") as wav:
        assert wav.getnchannels() == 1
        assert wav.getframerate() == 16000
    assert post.call_args.kwargs["json"] == {
        "model": "VoxCPM2",
        "input": "Hello",
        "voice": "default",
        "response_format": "wav",
        "stream": True,
    }
    assert post.call_args.kwargs["headers"]["Accept"] == "text/event-stream"
    response.close.assert_called_once()


def test_voxcpm_sends_reference_and_transcript_for_high_fidelity_clone(tmp_path):
    reference = tmp_path / "reference.wav"
    reference.write_bytes(_wav_bytes())
    task_df = Mock()
    response = SimpleNamespace(status_code=400, text="bad request", close=Mock())
    settings = {
        "api_key": "test-key",
        "model_id": "VoxCPM2",
        "mode": "high_fidelity",
    }
    with patch.object(voxcpm, "load_key_or", return_value=settings), patch.object(
        voxcpm, "_get_reference_context", return_value=(reference, "Original transcript.")
    ), patch.object(voxcpm, "_reference_audio_data_uri", return_value="data:audio/wav;base64,AA=="), patch.object(
        voxcpm.requests, "post", return_value=response
    ) as post:
        with pytest.raises(voxcpm.VoxCPMFatalError, match="400"):
            voxcpm.voxcpm_tts_for_videolingo("Translated", str(tmp_path / "out.wav"), 1, task_df)

    payload = post.call_args.kwargs["json"]
    assert payload["ref_audio"] == "data:audio/wav;base64,AA=="
    assert payload["prompt_audio"] == "data:audio/wav;base64,AA=="
    assert payload["prompt_text"] == "Original transcript."


def test_voxcpm_uses_uploaded_reference_and_manual_transcript(tmp_path):
    voxcpm.MANUAL_REFERENCE_AUDIO_PATH.parent.mkdir(parents=True)
    voxcpm.MANUAL_REFERENCE_AUDIO_PATH.write_bytes(_wav_bytes())
    response = SimpleNamespace(status_code=400, text="bad request", close=Mock())
    settings = {
        "api_key": "test-key",
        "model_id": "VoxCPM2",
        "mode": "high_fidelity",
        "prompt_text": "Exact uploaded transcript.",
    }
    with patch.object(voxcpm, "load_key_or", return_value=settings), patch.object(
        voxcpm, "_get_reference_context", side_effect=AssertionError("automatic reference used")
    ), patch.object(
        voxcpm, "_reference_audio_data_uri", return_value="data:audio/wav;base64,AA=="
    ), patch.object(voxcpm.requests, "post", return_value=response) as post:
        with pytest.raises(voxcpm.VoxCPMFatalError, match="400"):
            voxcpm.voxcpm_tts_for_videolingo("Translated", str(tmp_path / "out.wav"), 1, None)

    payload = post.call_args.kwargs["json"]
    assert payload["ref_audio"] == "data:audio/wav;base64,AA=="
    assert payload["prompt_audio"] == "data:audio/wav;base64,AA=="
    assert payload["prompt_text"] == "Exact uploaded transcript."


def test_voxcpm_uploaded_high_fidelity_reference_requires_transcript(tmp_path):
    voxcpm.MANUAL_REFERENCE_AUDIO_PATH.parent.mkdir(parents=True)
    voxcpm.MANUAL_REFERENCE_AUDIO_PATH.write_bytes(_wav_bytes())
    settings = {
        "api_key": "test-key",
        "model_id": "VoxCPM2",
        "mode": "high_fidelity",
        "prompt_text": "   ",
    }
    with patch.object(voxcpm, "load_key_or", return_value=settings), patch.object(
        voxcpm.requests, "post"
    ) as post:
        with pytest.raises(voxcpm.VoxCPMFatalError, match="exact transcript"):
            voxcpm.voxcpm_tts_for_videolingo("Translated", str(tmp_path / "out.wav"), 1, None)
    post.assert_not_called()


def test_voxcpm_voice_clone_sends_reference_without_transcript(tmp_path):
    reference = tmp_path / "reference.wav"
    reference.write_bytes(_wav_bytes())
    response = SimpleNamespace(status_code=400, text="bad request", close=Mock())
    settings = {"api_key": "test-key", "model_id": "VoxCPM2", "mode": "clone"}
    with patch.object(voxcpm, "load_key_or", return_value=settings), patch.object(
        voxcpm, "_get_reference_audio", return_value=(reference, 1)
    ), patch.object(
        voxcpm, "_reference_audio_data_uri", return_value="data:audio/wav;base64,AA=="
    ), patch.object(voxcpm.requests, "post", return_value=response) as post:
        with pytest.raises(voxcpm.VoxCPMFatalError, match="400"):
            voxcpm.voxcpm_tts_for_videolingo("Translated", str(tmp_path / "out.wav"), 1, None)

    payload = post.call_args.kwargs["json"]
    assert payload["ref_audio"] == "data:audio/wav;base64,AA=="
    assert "prompt_audio" not in payload
    assert "prompt_text" not in payload


def test_voxcpm_voice_clone_prefers_uploaded_reference(tmp_path):
    voxcpm.MANUAL_REFERENCE_AUDIO_PATH.parent.mkdir(parents=True)
    voxcpm.MANUAL_REFERENCE_AUDIO_PATH.write_bytes(_wav_bytes())
    response = SimpleNamespace(status_code=400, text="bad request", close=Mock())
    settings = {"api_key": "test-key", "model_id": "VoxCPM2", "mode": "clone"}
    with patch.object(voxcpm, "load_key_or", return_value=settings), patch.object(
        voxcpm, "_get_reference_audio", side_effect=AssertionError("automatic reference used")
    ), patch.object(
        voxcpm, "_reference_audio_data_uri", return_value="data:audio/wav;base64,AA=="
    ), patch.object(voxcpm.requests, "post", return_value=response) as post:
        with pytest.raises(voxcpm.VoxCPMFatalError, match="400"):
            voxcpm.voxcpm_tts_for_videolingo("Translated", str(tmp_path / "out.wav"), 1, None)

    payload = post.call_args.kwargs["json"]
    assert payload["ref_audio"] == "data:audio/wav;base64,AA=="
    assert "prompt_audio" not in payload
    assert "prompt_text" not in payload


def test_voxcpm_rejects_invalid_sse_audio(tmp_path):
    response = SimpleNamespace(
        status_code=200,
        iter_lines=lambda decode_unicode: _sse_lines(_event("speech.audio.delta", audio="not base64")),
        close=Mock(),
    )
    settings = {"api_key": "test-key", "model_id": "VoxCPM2", "mode": "default"}
    with patch.object(voxcpm, "load_key_or", return_value=settings), patch.object(
        voxcpm.requests, "post", return_value=response
    ):
        with pytest.raises(voxcpm.VoxCPMFatalError, match="Base64"):
            voxcpm.voxcpm_tts_for_videolingo("Hello", str(tmp_path / "out.wav"), 1, None)


def test_voxcpm_rejects_stream_without_done_event(tmp_path):
    response = SimpleNamespace(
        status_code=200,
        iter_lines=lambda decode_unicode: _sse_lines(
            _event("speech.audio.delta", audio=base64.b64encode(_streamed_wav_bytes()).decode())
        ),
        close=Mock(),
    )
    settings = {"api_key": "test-key", "model_id": "VoxCPM2", "mode": "default"}
    with patch.object(voxcpm, "load_key_or", return_value=settings), patch.object(
        voxcpm.requests, "post", return_value=response
    ):
        with pytest.raises(voxcpm.VoxCPMFatalError, match="speech.audio.done"):
            voxcpm.voxcpm_tts_for_videolingo("Hello", str(tmp_path / "out.wav"), 1, None)


def test_voxcpm_rejects_oversized_audio_response(tmp_path):
    oversized = b"x" * 32
    response = SimpleNamespace(
        status_code=200,
        iter_lines=lambda decode_unicode: _sse_lines(
            _event("speech.audio.delta", audio=base64.b64encode(oversized).decode()),
            _event("speech.audio.done"),
        ),
        close=Mock(),
    )
    settings = {"api_key": "test-key", "model_id": "VoxCPM2", "mode": "default"}
    with patch.object(voxcpm, "MAX_RESPONSE_AUDIO_BYTES", 16), patch.object(
        voxcpm, "load_key_or", return_value=settings
    ), patch.object(voxcpm.requests, "post", return_value=response):
        with pytest.raises(voxcpm.VoxCPMFatalError, match="100 MiB"):
            voxcpm.voxcpm_tts_for_videolingo("Hello", str(tmp_path / "out.wav"), 1, None)


def test_voxcpm_does_not_retry_authentication_errors(tmp_path):
    response = SimpleNamespace(status_code=401, text="invalid key", close=Mock())
    post = Mock(return_value=response)
    settings = {"api_key": "bad-key", "model_id": "VoxCPM2", "mode": "default"}
    with patch.object(voxcpm, "load_key_or", return_value=settings), patch.object(
        voxcpm.requests, "post", post
    ):
        with pytest.raises(voxcpm.VoxCPMFatalError, match="401"):
            voxcpm.voxcpm_tts_for_videolingo("Hello", str(tmp_path / "out.wav"), 1, None)
    post.assert_called_once()


def test_config_has_no_live_voxcpm_credentials_or_transcript():
    from ruamel.yaml import YAML

    config = YAML().load((Path(__file__).resolve().parents[1] / "config.yaml").read_text(encoding="utf-8"))
    assert config["voxcpm"]["api_key"] == ""
    assert config["voxcpm"]["model_id"] == "VoxCPM2"
    assert config["voxcpm"]["mode"] in voxcpm.VOXCPM_MODES
    assert config["voxcpm"]["prompt_text"] == ""


@pytest.mark.parametrize(
    ("settings", "expected"),
    [
        ({"mode": "default"}, "default"),
        ({"mode": "clone"}, "clone"),
        ({"mode": "high_fidelity"}, "high_fidelity"),
        ({"high_fidelity": True}, "high_fidelity"),
        ({"high_fidelity": False}, "default"),
        ({}, "clone"),
    ],
)
def test_voxcpm_mode_resolution(settings, expected):
    assert voxcpm._resolve_mode(settings) == expected


def test_reference_context_rejects_missing_transcript(tmp_path, monkeypatch):
    import pandas as pd

    reference = tmp_path / "output" / "audio" / "refers" / "1.wav"
    reference.parent.mkdir(parents=True)
    reference.write_bytes(_wav_bytes())
    task_df = pd.DataFrame([{"number": 1, "origin": float("nan")}])
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="source transcript"):
        voxcpm._get_reference_context(1, task_df)


def test_reference_context_prefers_current_segment_after_extraction(tmp_path, monkeypatch):
    import pandas as pd
    from core import _9_refer_audio

    refers = tmp_path / "output" / "audio" / "refers"
    task_df = pd.DataFrame(
        [
            {"number": 1, "origin": "First transcript."},
            {"number": 2, "origin": "Current transcript."},
        ]
    )

    def extract():
        refers.mkdir(parents=True)
        (refers / "1.wav").write_bytes(_wav_bytes())
        (refers / "2.wav").write_bytes(_wav_bytes())

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(_9_refer_audio, "extract_refer_audio_main", extract)
    path, text = voxcpm._get_reference_context(2, task_df)
    assert path.name == "2.wav"
    assert text == "Current transcript."
