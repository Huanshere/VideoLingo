"""Fish Audio, the official API: the requests of the backend (offline, the HTTP call is replaced)."""
import struct
import wave

import msgpack
import pandas as pd
import pytest
from pydub import AudioSegment

from core.tts_backend import fish_audio_tts as fish


def _streamed_wav(seconds=1.0, rate=44100):
    """A WAV as the API streams it: the two lengths of the header are placeholders."""
    samples = b"\x01\x00" * int(seconds * rate)
    header = (b"RIFF" + struct.pack("<I", 0xFFFFFF24) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, rate, rate * 2, 2, 16)
              + b"data" + struct.pack("<I", 0xFFFFFF00))
    return header + samples


class _Answer:
    def __init__(self, status_code=200, content=b"", text=""):
        self.status_code, self.content, self.text = status_code, content, text


class _Service:
    """Stands for requests.post and keeps what was sent."""

    def __init__(self, answer):
        self.answer, self.calls = answer, []

    def __call__(self, url, headers=None, data=None, timeout=None):
        self.calls.append({"url": url, "headers": headers, "body": msgpack.unpackb(data, raw=False)})
        return self.answer


@pytest.fixture
def video(monkeypatch, tmp_path):
    """Three lines of a video with their reference clips of 6, 7 and 8 seconds."""
    refers = tmp_path / "refers"
    refers.mkdir()
    for number, seconds in ((1, 6), (2, 7), (4, 8)):
        AudioSegment.silent(duration=seconds * 1000, frame_rate=32000).export(refers / f"{number}.wav", format="wav")
    monkeypatch.setattr(fish, "_AUDIO_REFERS_DIR", str(refers))
    monkeypatch.setattr("time.sleep", lambda seconds: None)
    return pd.DataFrame({"number": [1, 2, 4], "origin": ["First line.", "Second line.", "Third line."]})


def _use(monkeypatch, answer, **settings):
    service = _Service(answer)
    config = {"api_key": "test-key", "mode": "clone", "voice_id": "", "model": "s2.1-pro", **settings}
    monkeypatch.setattr(fish, "load_key", lambda key: config)
    monkeypatch.setattr(fish.requests, "post", service)
    return service


def _seconds(wav_bytes, tmp_path):
    path = tmp_path / "sent.wav"
    path.write_bytes(wav_bytes)
    with wave.open(str(path)) as audio:
        return audio.getnframes() / audio.getframerate()


def test_refused_request_is_an_error_and_leaves_no_file(monkeypatch, tmp_path, video):
    service = _use(monkeypatch, _Answer(401, text='{"status": 401, "message": "Invalid API key"}'))
    audio = tmp_path / "1.wav"

    with pytest.raises(ValueError, match="HTTP 401.*Invalid API key"):
        fish.fish_audio_tts("你好", str(audio), 1, video)

    assert not audio.exists()
    assert len(service.calls) == 4  # the first request and 3 retries


def test_answer_without_audio_is_an_error(monkeypatch, tmp_path, video):
    _use(monkeypatch, _Answer(200, content=b""))
    audio = tmp_path / "1.wav"

    with pytest.raises(ValueError, match="without audio"):
        fish.fish_audio_tts("你好", str(audio), 1, video)

    assert not audio.exists()


def test_clone_sends_one_reference_of_the_video_with_its_text(monkeypatch, tmp_path, video):
    service = _use(monkeypatch, _Answer(200, content=_streamed_wav(1.0)))
    audio = tmp_path / "segs" / "2.wav"

    fish.fish_audio_tts("第二句", str(audio), 2, video)

    call = service.calls[0]
    assert call["url"] == "https://api.fish.audio/v1/tts"
    assert call["headers"]["Authorization"] == "Bearer test-key"
    assert call["headers"]["Content-Type"] == "application/msgpack"
    assert call["headers"]["model"] == "s2.1-pro"
    body = call["body"]
    assert body["text"] == "第二句" and body["format"] == "wav"
    assert "reference_id" not in body
    # 6 + 7 + 8 s: the third clip is needed to reach 15 s, and the text follows the audio
    (reference,) = body["references"]
    assert reference["text"] == "First line. Second line. Third line."
    assert reference["audio"][:4] == b"RIFF"
    assert _seconds(reference["audio"], tmp_path) == pytest.approx(21, abs=0.01)
    # The file that is written has its real length in the header
    with wave.open(str(audio)) as written:
        assert written.getnframes() / written.getframerate() == pytest.approx(1.0)


def test_reference_stays_within_30_seconds(monkeypatch, tmp_path):
    refers = tmp_path / "refers"
    refers.mkdir()
    for number, seconds in ((1, 12), (2, 20), (3, 5)):
        AudioSegment.silent(duration=seconds * 1000, frame_rate=16000).export(refers / f"{number}.wav", format="wav")
    monkeypatch.setattr(fish, "_AUDIO_REFERS_DIR", str(refers))
    tasks = pd.DataFrame({"number": [1, 2, 3], "origin": ["One.", "Two.", "Three."]})

    audio, text = fish.stable_reference(tasks)

    assert text == "One."  # 12 + 20 s would be more than 30 s
    assert _seconds(audio, tmp_path) == pytest.approx(12, abs=0.01)


def test_missing_reference_clips_are_an_error(monkeypatch, tmp_path):
    monkeypatch.setattr(fish, "_AUDIO_REFERS_DIR", str(tmp_path))
    with pytest.raises(FileNotFoundError):
        fish.stable_reference(pd.DataFrame({"number": [1], "origin": ["One."]}))


def test_preset_sends_the_voice_id_and_no_reference(monkeypatch, tmp_path, video):
    service = _use(monkeypatch, _Answer(200, content=_streamed_wav()), mode="preset", voice_id=" 7f92f8afb8ec43bf81429cc1c9199cb1 ",
                   model="s1")
    audio = tmp_path / "1.wav"

    fish.fish_audio_tts("你好", str(audio), 1, video)

    call = service.calls[0]
    assert call["body"]["reference_id"] == "7f92f8afb8ec43bf81429cc1c9199cb1"
    assert "references" not in call["body"]
    assert call["headers"]["model"] == "s1"
    assert audio.exists()


@pytest.mark.parametrize("entered,voice_id", [
    ("74c6aba5cbf94a15bbdc547ffce5cb38", "74c6aba5cbf94a15bbdc547ffce5cb38"),
    (" https://fish.audio/m/74c6aba5cbf94a15bbdc547ffce5cb38/ ", "74c6aba5cbf94a15bbdc547ffce5cb38"),
    ("https://fish.audio/zh-CN/m/74C6ABA5CBF94A15BBDC547FFCE5CB38?from=share", "74c6aba5cbf94a15bbdc547ffce5cb38"),
    ("my-voice", "my-voice"),
    ("", ""),
    (None, ""),
])
def test_voice_id_is_taken_from_the_id_or_from_the_address_of_the_voice(entered, voice_id):
    assert fish.voice_id_of(entered) == voice_id


def test_voices_of_the_config_are_ids_and_the_default_is_one_of_them():
    from core.utils.config_utils import load_key

    voices = load_key("fish_audio.voices")
    assert len(set(voices.values())) == len(voices) >= 2
    assert all(fish.VOICE_ID.fullmatch(voice_id) for voice_id in voices.values())
    assert load_key("fish_audio.voice_id") in voices.values()
    assert load_key("fish_audio.mode") == "clone" and load_key("fish_audio.model") == "s2.1-pro"


@pytest.mark.parametrize("settings,message", [
    ({"mode": "preset", "voice_id": ""}, "voice id"),
    ({"mode": "unknown"}, "Invalid Fish Audio mode"),
    ({"api_key": "YOUR_FISH_AUDIO_KEY"}, "API key is missing"),
])
def test_incomplete_settings_are_an_error_without_a_request(monkeypatch, tmp_path, video, settings, message):
    service = _use(monkeypatch, _Answer(200, content=_streamed_wav()), **settings)
    audio = tmp_path / "1.wav"

    with pytest.raises(ValueError, match=message):
        fish.fish_audio_tts("你好", str(audio), 1, video)

    assert service.calls == [] and not audio.exists()


def test_dubbing_uses_the_backend_for_the_method_fish_audio(monkeypatch, tmp_path):
    from core.tts_backend import tts_main

    sent = []

    def speak(text, save_as, number, task_df):
        sent.append((text, number))
        AudioSegment.silent(duration=500).export(save_as, format="wav")

    monkeypatch.setattr(tts_main, "load_key", lambda key: "fish_audio")
    monkeypatch.setattr(tts_main, "fish_audio_tts", speak)
    monkeypatch.setattr(tts_main, "get_audio_duration", lambda path: 0.5)

    tts_main.tts_main("你好世界", str(tmp_path / "7.wav"), 7, None)

    assert sent == [("你好世界", 7)]


def test_fish_audio_is_a_provider_with_its_own_key():
    from core.st_utils.tts_settings import KEY_PATHS, PROVIDERS, configured_keys

    assert PROVIDERS["Fish Audio"] == ("fish_audio",)
    assert KEY_PATHS["Fish Audio"] == ("fish_audio.api_key",)
    assert configured_keys("Fish Audio", "fish_audio", {"fish_audio.api_key": "abc"}.get) == ("abc", False)
    # The key of 302.ai is not offered for Fish Audio
    assert "fish_audio.api_key" not in KEY_PATHS["302.ai"]


def test_settings_are_saved_into_a_config_without_the_section(monkeypatch, tmp_path):
    from core.st_utils.tts_settings import save_provider_key, save_settings
    from core.utils import config_utils

    config = tmp_path / "config.yaml"
    config.write_text("tts_method: 'edge_tts'  # kept\n", encoding="utf-8")
    monkeypatch.setattr(config_utils, "CONFIG_PATH", str(config))

    save_provider_key("Fish Audio", "abc")
    save_settings({"fish_audio.mode": "preset", "fish_audio.voice_id": "123"})

    assert config_utils.load_key("fish_audio") == {"api_key": "abc", "mode": "preset", "voice_id": "123"}
    assert "# kept" in config.read_text(encoding="utf-8")


@pytest.mark.parametrize("method,boxes", [("fish_audio", ["TTS Provider"]),
                                          ("sf_fish_tts", ["TTS Provider", "TTS Method"])])
def test_provider_with_one_method_has_no_method_box(monkeypatch, method, boxes):
    from streamlit.testing.v1 import AppTest
    from core.utils import config_utils
    from translations import translations

    monkeypatch.setattr(config_utils, "load_key", lambda key: method)
    monkeypatch.setattr(config_utils, "load_key_or", lambda key, default: default)
    monkeypatch.setattr(translations, "translate", lambda text: text)

    def page():
        from core.st_utils.tts_settings import PROVIDERS, select_tts_method
        select_tts_method({name: name for methods in PROVIDERS.values() for name in methods})

    app = AppTest.from_function(page, default_timeout=30).run()

    assert not app.exception
    assert [box.label for box in app.selectbox] == boxes
