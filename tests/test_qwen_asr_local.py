"""Offline checks for the Qwen3-ASR + ForcedAligner backend (no model downloads, no inference)."""
import subprocess
import sys
import types
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest

from core.asr_backend import qwen_asr_local as qwen
from core.asr_backend import transcription_cache as cache


def words(text, tokens, offset=0.0):
    items = [(token, i, i + 0.5) for i, token in enumerate(tokens)]
    return [w["word"] for w in qwen.attach_words(text, items, offset)]


# ------------------------------------------------------------------
# attach_words: aligner tokens have punctuation stripped; words must get it back
# ------------------------------------------------------------------

@pytest.mark.parametrize("text,tokens,expected", [
    ("Hello, world.", ["Hello", "world"], ["Hello,", "world."]),
    ("你好，世界。", ["你", "好", "世", "界"], ["你", "好，", "世", "界。"]),
    ("我用Python写代码。", ["我", "用", "Python", "写", "代", "码"], ["我", "用", "Python", "写", "代", "码。"]),
    ("The U.S., at 3.5 percent.", ["The", "US", "at", "35", "percent"], ["The", "U.S.,", "at", "3.5", "percent."]),
    ("Don't stop!", ["Don't", "stop"], ["Don't", "stop!"]),
    ('"Hi," she said.', ["Hi", "she", "said"], ['"Hi,"', "she", "said."]),
    ("Really ?", ["Really"], ["Really?"]),
])
def test_attach_words_restores_punctuation(text, tokens, expected):
    assert words(text, tokens) == expected


def test_attach_words_keeps_tokens_joinable_with_spacy_splitting():
    text = "Hello, world. This is Qwen."
    assert " ".join(words(text, ["Hello", "world", "This", "is", "Qwen"])) == text


def test_long_surface_falls_back_to_bare_token():
    token = "a" * 29
    assert words(token + "!!!", [token]) == [token]


def test_unmatched_token_is_kept_without_consuming_transcript():
    assert words("Hello, world.", ["Hello", "zzz", "world"]) == ["Hello,", "zzz", "world."]


def test_empty_tokens_are_skipped():
    assert words("Hi there", ["", "Hi", "there"]) == ["Hi", "there"]


def test_timestamps_offset_clamped_and_monotonic_per_word():
    result = qwen.attach_words("a b", [("a", -0.2, 0.4), ("b", 1.0, 0.8)], offset=10)
    assert result == [{"word": "a", "start": 10.0, "end": 10.4}, {"word": "b", "start": 11.0, "end": 11.0}]


# ------------------------------------------------------------------
# split_windows
# ------------------------------------------------------------------

def test_short_audio_is_one_window():
    assert qwen.split_windows(np.zeros(16000 * 5, dtype=np.float32)) == [(0, 16000 * 5)]
    assert qwen.split_windows(np.zeros(0, dtype=np.float32)) == [(0, 0)]


def test_exact_window_length_is_not_split():
    sr = 100
    assert qwen.split_windows(np.ones(180 * sr, dtype=np.float32), sr=sr) == [(0, 180 * sr)]


def test_long_audio_windows_are_contiguous_bounded_and_cut_at_silence():
    sr = 100  # small rate keeps the test fast; the algorithm is rate independent
    rng = np.random.default_rng(0)
    wav = rng.uniform(0.2, 1.0, 500 * sr).astype(np.float32)
    wav[170 * sr:171 * sr] = 0  # quiet spot inside the first window's search range
    windows = qwen.split_windows(wav, sr=sr)
    assert windows[0][0] == 0 and windows[-1][1] == len(wav)
    assert all(a[1] == b[0] for a, b in zip(windows, windows[1:]))
    assert all(0 < end - start <= 180 * sr for start, end in windows)
    assert 170 * sr <= windows[0][1] <= 171 * sr
    for start, end in windows[:-1]:
        assert end >= start + (180 - 30) * sr


# ------------------------------------------------------------------
# Language mapping
# ------------------------------------------------------------------

def test_language_mapping():
    assert qwen.qwen_language("auto") is None and qwen.qwen_language(None) is None
    assert qwen.qwen_language("zh") == "Chinese" and qwen.qwen_language("ja") == "Japanese"
    with pytest.raises(ValueError, match="does not support"):
        qwen.qwen_language("xx")
    assert qwen.iso_language("Chinese,English") == "zh"
    assert qwen.iso_language("cantonese") == "zh"
    assert qwen.iso_language(" english ") == "en"
    assert qwen.iso_language("") is None and qwen.iso_language(None) is None
    assert qwen.iso_language("Klingon") is None


def test_language_table_matches_qwen_supported_languages():
    # qwen_asr.inference.utils.SUPPORTED_LANGUAGES (qwen-asr 0.0.6)
    supported = {"Chinese", "English", "Cantonese", "Arabic", "German", "French", "Spanish", "Portuguese",
                 "Indonesian", "Italian", "Korean", "Russian", "Thai", "Vietnamese", "Japanese", "Turkish",
                 "Hindi", "Malay", "Dutch", "Swedish", "Danish", "Finnish", "Polish", "Czech", "Filipino",
                 "Persian", "Greek", "Romanian", "Hungarian", "Macedonian"}
    assert set(qwen.ISO_TO_QWEN.values()) == supported
    # Every recognition language offered in the sidebar must be accepted.
    for code in ("en", "zh", "es", "ru", "fr", "de", "it", "ja"):
        assert qwen.qwen_language(code) in supported


# ------------------------------------------------------------------
# Engine / model selection
# ------------------------------------------------------------------

@pytest.fixture
def platform_env(monkeypatch):
    def configure(apple, installed):
        monkeypatch.setattr(qwen, "_apple_silicon", lambda: apple)
        monkeypatch.setattr(qwen, "_installed", lambda module: module in installed)
    return configure


@pytest.mark.parametrize("apple,installed,requested,expected", [
    (True, {"mlx_audio"}, "auto", "mlx"),
    (True, {"mlx_audio", "qwen_asr"}, "auto", "mlx"),
    (True, {"qwen_asr"}, "auto", "transformers"),
    (False, {"qwen_asr"}, "auto", "transformers"),
    (False, {"qwen_asr", "mlx_audio"}, "AUTO", "transformers"),
    (True, {"mlx_audio", "qwen_asr"}, "transformers", "transformers"),
    (True, {"mlx_audio"}, "mlx", "mlx"),
])
def test_resolve_engine(platform_env, apple, installed, requested, expected):
    platform_env(apple, installed)
    assert qwen.resolve_engine(requested) == expected


@pytest.mark.parametrize("apple,installed,requested,package", [
    (False, set(), "auto", "qwen-asr"),
    # Apple Silicon requirements install mlx-audio; never tell a Mac user to install qwen-asr.
    (True, set(), "auto", "mlx-audio"),
    (True, {"mlx_audio"}, "transformers", "qwen-asr"),
    (False, {"qwen_asr"}, "mlx", "mlx-audio"),
])
def test_missing_engine_package_explains_fix(platform_env, apple, installed, requested, package):
    platform_env(apple, installed)
    with pytest.raises(ImportError, match=package) as error:
        qwen.resolve_engine(requested)
    assert "installer.py" in str(error.value) and "whisperx" in str(error.value)


def test_invalid_engine_and_model_size(platform_env):
    platform_env(False, {"qwen_asr"})
    with pytest.raises(ValueError, match="qwen_engine"):
        qwen.resolve_engine("vllm")
    assert qwen.model_size("1.7B") == "1.7b" and qwen.model_size("0.6b") == "0.6b"
    with pytest.raises(ValueError, match="qwen_model"):
        qwen.model_size("4b")


def test_configured_defaults_are_used(monkeypatch, platform_env):
    platform_env(False, {"qwen_asr"})
    monkeypatch.setattr(qwen, "load_key_or", lambda key, default: default)
    assert qwen.model_size() == "1.7b"
    assert qwen.resolve_engine() == "transformers"


def test_model_source_prefers_complete_local_copy(monkeypatch, tmp_path):
    monkeypatch.setattr(qwen, "load_key", lambda key: str(tmp_path))
    assert qwen._model_source("Qwen/Qwen3-ASR-1.7B") == "Qwen/Qwen3-ASR-1.7B"
    (tmp_path / "Qwen3-ASR-1.7B").mkdir()
    assert qwen._model_source("Qwen/Qwen3-ASR-1.7B") == "Qwen/Qwen3-ASR-1.7B"
    (tmp_path / "Qwen3-ASR-1.7B" / "config.json").write_text("{}")
    assert qwen._model_source("Qwen/Qwen3-ASR-1.7B") == str((tmp_path / "Qwen3-ASR-1.7B").resolve())


def test_model_table():
    for engine, models in qwen.MODELS.items():
        assert set(models) == {"1.7b", "0.6b", "aligner"}
        assert "ForcedAligner-0.6B" in models["aligner"]
        assert all(("8bit" in repo) == (engine == "mlx") for repo in models.values())


# ------------------------------------------------------------------
# transcribe_audio with the engines mocked out
# ------------------------------------------------------------------

SR = qwen.SAMPLE_RATE


RAW_BASE, VOCAL_BASE = 0.0, 1000.0  # sample value = seconds (+ base): fakes can tell where a clip starts


def ramp(seconds, base):
    return (base + np.arange(int(seconds * SR), dtype=np.float64) / SR).astype(np.float32)


@pytest.fixture
def pipeline(monkeypatch):
    """Mock config, audio decoding and both engines.

    state["asr"](start_s, end_s, language) plays the model for a clip of the raw ramp;
    state["calls"]["asr"] records (start_s, seconds, language) for every ASR call.
    """
    state = {"language": "en", "asr": None, "calls": {"asr": []}}
    # A rising ramp puts the lowest energy at the start of each cut search range: windows 0-150 s, 150-200 s.
    audio = state["audio"] = {"raw.wav": ramp(200, RAW_BASE), "vocal.mp3": ramp(200, VOCAL_BASE)}

    monkeypatch.setattr(qwen, "resolve_engine", lambda requested=None: "transformers")
    monkeypatch.setattr(qwen, "model_size", lambda requested=None: "0.6b")
    monkeypatch.setattr(qwen, "load_key", lambda key: {"whisper.language": state["language"]}[key])
    monkeypatch.setattr(qwen, "load_audio_segment", lambda path, start, end: audio[path])

    @contextmanager
    def session(engine, repo_id):
        state["calls"]["session"] = (engine, repo_id)

        def run(clip, language):
            begin = round(float(clip[0]) - RAW_BASE, 2)
            state["calls"]["asr"].append((begin, len(clip) / SR, language))
            return state["asr"](begin, begin + len(clip) / SR, language)
        yield run

    def align(engine, repo_id, jobs):
        state["calls"]["align"] = (engine, repo_id, [(round(float(c[0]), 2), text, lang) for c, text, lang in jobs])
        state["calls"]["align_lengths"] = [len(c) for c, _, _ in jobs]
        return [[(tok, 0.5 + i, 1.0 + i) for i, tok in enumerate(text.rstrip(".").replace(",", "").split())]
                for _, text, _ in jobs]

    monkeypatch.setattr(qwen, "asr_session", session)
    monkeypatch.setattr(qwen, "_align", align)
    return state


def window_calls(state):
    return [call for call in state["calls"]["asr"] if call[2] is not None]


ZH = "我们今天开一个meeting，然后presentation要准备好，客户那边说要double check一下细节。"


def test_transcribe_audio_structure_offsets_and_cache_validity(pipeline):
    pipeline["asr"] = lambda a, b, language: (language, "Hello, world." if a < 1 else "Bye now.")
    result = qwen.transcribe_audio("raw.wav", "vocal.mp3", 60, 260)

    assert pipeline["calls"]["session"] == ("transformers", "Qwen/Qwen3-ASR-0.6B")
    calls = window_calls(pipeline)
    # Forced language: one call per window with the language (no retry).
    assert [language for *_, language in calls] == ["English", "English"]
    lengths = [seconds for _, seconds, _ in calls]
    assert sum(lengths) == pytest.approx(200) and max(lengths) <= 180
    engine, repo, jobs = pipeline["calls"]["align"]
    assert repo == "Qwen/Qwen3-ForcedAligner-0.6B"
    # Alignment runs on the vocal track (same sample indices) with the forced language.
    assert [(c, lang) for c, _, lang in jobs] == [(VOCAL_BASE, "English"), (VOCAL_BASE + calls[1][0], "English")]

    assert result["language"] == "en"
    first, second = result["segments"]
    assert first["text"] == "Hello, world." and [w["word"] for w in first["words"]] == ["Hello,", "world."]
    assert first["words"][0] == {"word": "Hello,", "start": 60.5, "end": 61.0}
    assert second["words"][0]["start"] == pytest.approx(60 + calls[1][0] + 0.5, abs=1e-3)
    assert first["start"] == first["words"][0]["start"] and second["end"] == second["words"][-1]["end"]
    assert cache.valid_result(result)


def code_switched(a, b, language):
    """1.7B on the Mini: an opening clip is heard as English and loops; forcing Chinese works."""
    if language is None:
        return ("English", "Yeah, yeah, yeah.") if a < 30 else ("Chinese,English", ZH)
    if language == "English":
        return "English", "Yeah, yeah. " * 500
    return language, ZH * max(1, int((b - a) // 10))


def test_auto_probes_vote_then_force_the_language(pipeline):
    pipeline["language"] = "auto"
    pipeline["asr"] = code_switched
    result = qwen.transcribe_audio("raw.wav", "raw.wav", 0, 200)
    probes = [call for call in pipeline["calls"]["asr"] if call[2] is None]
    # 150 s window: 3 probes of 20 s spread over it; 50 s window: 2 probes.
    assert [a for a, _, _ in probes[:3]] == pytest.approx([15, 65, 115], abs=0.1)
    assert len(probes) == 5 and all(s == 20 for _, s, _ in probes)
    # One misleading English probe is outvoted; each window is transcribed with Chinese forced.
    assert [language for *_, language in window_calls(pipeline)] == ["Chinese", "Chinese"]
    assert result["language"] == "zh"
    assert [lang for *_, lang in pipeline["calls"]["align"][2]] == ["Chinese", "Chinese"]


def test_degenerate_window_is_retried_in_shorter_windows(pipeline):
    pipeline["language"] = "zh"

    def asr(a, b, language):
        if b - a > qwen.RETRY_WINDOW_SECONDS + 1:
            return language, "谢谢大家。" * 300  # loops on the long window
        return language, ZH
    pipeline["asr"] = asr
    result = qwen.transcribe_audio("raw.wav", "raw.wav", 0, 200)
    first_window = [(a, s) for a, s, _ in window_calls(pipeline) if a < 150]
    assert first_window[0][1] == pytest.approx(150, abs=0.1)  # the long attempt
    retries = [s for _, s in first_window[1:]]
    assert len(retries) >= 3 and max(retries) <= qwen.RETRY_WINDOW_SECONDS and sum(retries) == pytest.approx(150, abs=0.1)
    assert all(segment["text"] == ZH for segment in result["segments"])
    assert len(result["segments"]) == len(retries) + 1  # the 50 s window was fine on its own


def test_still_degenerate_after_retry_fails_loudly(pipeline):
    pipeline["language"] = "zh"
    pipeline["asr"] = lambda a, b, language: (language, "谢谢大家。" * 300)
    with pytest.raises(ValueError, match=r"0\.0-150\.\d+s is still degenerate.*recognition language"):
        qwen.transcribe_audio("raw.wav", "raw.wav", 0, 200)


def test_too_little_text_compared_with_probes_fails_loudly(pipeline):
    # The Mini's 120 s result: 3 words although probes heard a lot of speech.
    pipeline["language"] = "auto"
    pipeline["asr"] = lambda a, b, language: (
        ("Chinese", ZH) if language is None else ("Chinese", "对。"))
    with pytest.raises(ValueError, match=r"still degenerate after retrying \(only \d+ letters/digits, while shorter probe clips"):
        qwen.transcribe_audio("raw.wav", "raw.wav", 0, 200)


def test_silence_and_music_intro_is_not_flagged(pipeline):
    # 60 s of silence/music hears nothing: probes are empty there, the window text is normal.
    pipeline["language"] = "auto"

    def asr(a, b, language):
        speech = b > 60
        if language is None:
            return ("Chinese", ZH) if a >= 60 else ("", "")
        return language, ZH * 3 if speech else ""
    pipeline["asr"] = asr
    result = qwen.transcribe_audio("raw.wav", "raw.wav", 0, 200)
    assert len(window_calls(pipeline)) == 2  # one call per window: no retry
    assert result["language"] == "zh" and len(result["segments"]) == 2


def test_music_only_window_follows_segment_language(pipeline):
    pipeline["language"] = "auto"
    pipeline["asr"] = lambda a, b, language: (
        ("English", "One two three four five six seven.") if language is None and a < 150 else
        ("", "") if language is None else (language, "One two three four five six seven. Then eight, nine and ten." if a < 150 else ""))
    result = qwen.transcribe_audio("raw.wav", "raw.wav", 0, 200)
    # The second window's probes heard nothing; it is still transcribed with the segment's language.
    assert [language for *_, language in window_calls(pipeline)] == ["English", "English"]
    assert result["language"] == "en" and len(result["segments"]) == 1


def test_undetectable_language_asks_user_to_set_it(pipeline):
    pipeline["language"] = "auto"
    pipeline["asr"] = lambda a, b, language: ("", "???")
    with pytest.raises(ValueError, match="(?i)set the recognition language"):
        qwen.transcribe_audio("raw.wav", "raw.wav", 0, 200)


def test_silence_returns_empty_segments_without_loading_aligner(pipeline):
    pipeline["language"] = "auto"
    pipeline["asr"] = lambda a, b, language: ("", "")
    result = qwen.transcribe_audio("raw.wav", "raw.wav", 0, 200)
    assert result == {"language": None, "segments": []}
    assert "align" not in pipeline["calls"]


@pytest.mark.parametrize("vocal_seconds", [150, 200.5])
def test_vocal_track_is_matched_to_raw_length(pipeline, vocal_seconds):
    # Re-encoded Demucs vocals can decode shorter or longer than the raw track.
    pipeline["audio"]["vocal.mp3"] = ramp(vocal_seconds, VOCAL_BASE)
    pipeline["asr"] = lambda a, b, language: (language, "One." if a < 1 else "Two.")
    result = qwen.transcribe_audio("raw.wav", "vocal.mp3", 0, 200)
    assert pipeline["calls"]["align_lengths"] == [round(s * SR) for _, s, _ in window_calls(pipeline)]
    assert len(result["segments"]) == 2


# ------------------------------------------------------------------
# Degenerate-output heuristics
# ------------------------------------------------------------------

@pytest.mark.parametrize("text,expected", [
    ("Yeah, yeah. " * 500, True),                                    # Mini: 6138 chars of this
    ("今天我们聊一聊怎么准备面试。" + "谢谢大家。" * 40, True),          # loops after a normal start
    ("Yeah, yeah, yeah.", False),                                    # too short to judge by itself
    ("if you if you if you if you want to know why they do what they do, ask them directly", False),
    ("哈哈哈哈哈哈哈哈 这个太好笑了", False),
    (ZH * 3, False),                                                 # the same sentence 3x is not a loop
])
def test_is_repetitive(text, expected):
    assert qwen.is_repetitive(text) is expected


def test_is_repetitive_ignores_real_documents():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    for name in ("README.md", "translations/README.zh.md", "translations/README.ja.md", "translations/README.ru.md"):
        assert not qwen.is_repetitive((root / name).read_text(encoding="utf-8")), name


def test_degeneration_uses_probe_text_as_reference():
    heard = [ZH, ZH]
    assert qwen.degeneration("Yeah, yeah, yeah.") is None
    assert "letters/digits" in qwen.degeneration("对。", heard)
    assert qwen.degeneration(ZH * 2, heard) is None
    assert qwen.degeneration("对。", ["嗯。"]) is None   # probes heard too little to judge


def test_vote_and_probe_ranges():
    assert qwen._vote([]) is None
    assert qwen._vote([("English", "Yeah."), ("Chinese", ZH), ("Chinese", ZH)]) == "Chinese"
    assert qwen._vote([("English", "short"), ("Chinese", ZH)]) == "Chinese"  # tie -> more text
    assert qwen.probe_ranges(25 * SR) == [(0, 25 * SR)]
    assert qwen.probe_ranges(180 * SR) == [(20 * SR, 40 * SR), (80 * SR, 100 * SR), (140 * SR, 160 * SR)]
    for a, b in qwen.probe_ranges(45 * SR):
        assert 0 <= a < b <= 45 * SR and b - a == 20 * SR


def test_primary_language():
    assert qwen.primary_language("Chinese,English") == "Chinese"
    assert qwen.primary_language("cantonese") == "Cantonese" and qwen.iso_language("Cantonese") == "zh"
    assert qwen.primary_language("Klingon") is None and qwen.primary_language(None) is None


def test_match_length():
    wav = np.arange(5, dtype=np.float32)
    assert qwen.match_length(wav, 3).tolist() == [0, 1, 2]
    assert qwen.match_length(wav, 7).tolist() == [0, 1, 2, 3, 4, 0, 0]
    assert qwen.match_length(wav, 7).dtype == np.float32


# ------------------------------------------------------------------
# FFmpeg decoding
# ------------------------------------------------------------------

def test_load_audio_segment_decodes_16k_mono(tmp_path):
    path = tmp_path / "tone.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=3",
                    "-ac", "2", "-ar", "44100", str(path)], check=True)
    wav = qwen.load_audio_segment(path, 1, 2)
    assert wav.dtype == np.float32 and abs(len(wav) - SR) <= SR // 100


def test_load_audio_segment_reports_ffmpeg_stderr(tmp_path):
    with pytest.raises(RuntimeError, match="FFmpeg could not decode") as error:
        qwen.load_audio_segment(tmp_path / "missing.wav", 0, 1)
    assert "missing.wav" in str(error.value).split("):", 1)[1]


# ------------------------------------------------------------------
# Engine wiring against fake qwen-asr / mlx-audio / torch modules
# ------------------------------------------------------------------

@pytest.fixture
def engines(monkeypatch):
    """Install fake engine modules; record constructor and call arguments."""
    calls = {"free": Mock()}
    monkeypatch.setattr(qwen, "_model_source", lambda repo_id: "src:" + repo_id)
    monkeypatch.setattr(qwen, "_torch_device", lambda: ("cuda:0", "bf16"))
    monkeypatch.setattr(qwen, "_free", calls["free"])
    monkeypatch.setattr(qwen, "check_cancel", lambda: None)
    item = lambda text, a, b: SimpleNamespace(text=text, start_time=a, end_time=b)

    class ASRModel:
        @classmethod
        def from_pretrained(cls, source, **kwargs):
            calls["asr_load"] = (source, kwargs)
            return cls()

        def transcribe(self, audio, language=None):
            calls.setdefault("asr", []).append((audio[1], len(audio[0]), language))
            calls.setdefault("asr_tokens", []).append(self.max_new_tokens)
            if calls.get("fail"):
                raise RuntimeError("CUDA out of memory")
            return [SimpleNamespace(language="English", text=" Hello, world. ")]

    class Aligner:
        @classmethod
        def from_pretrained(cls, source, **kwargs):
            calls["align_load"] = (source, kwargs)
            return cls()

        def align(self, audio, text, language):
            calls.setdefault("align", []).append((audio[1], text, language))
            if calls.get("fail"):
                raise RuntimeError("alignment failed")
            return [[item("Hello", 0.1, 0.4), item("world", 0.5, 0.9)]]

    class MLXModel:
        def __init__(self, source):
            self.source = source

        def generate(self, audio, **kwargs):
            calls.setdefault("mlx", []).append((self.source, len(audio), kwargs))
            if calls.get("fail"):
                raise RuntimeError("metal out of memory")
            if "text" in kwargs:  # forced aligner
                return iter([item("你", 0.0, 0.2), item("好", 0.2, 0.4)])
            return SimpleNamespace(text=" 你好。 ", language=["Chinese", "Chinese"])

    qwen_asr = types.ModuleType("qwen_asr")
    qwen_asr.Qwen3ASRModel, qwen_asr.Qwen3ForcedAligner = ASRModel, Aligner
    utils = types.ModuleType("mlx_audio.stt.utils")
    utils.load_model = MLXModel
    monkeypatch.setitem(sys.modules, "qwen_asr", qwen_asr)
    monkeypatch.setitem(sys.modules, "mlx_audio", types.ModuleType("mlx_audio"))
    monkeypatch.setitem(sys.modules, "mlx_audio.stt", types.ModuleType("mlx_audio.stt"))
    monkeypatch.setitem(sys.modules, "mlx_audio.stt.utils", utils)
    return calls


CLIPS = [np.zeros(SR, dtype=np.float32), np.zeros(SR // 10, dtype=np.float32)]


def test_transformers_transcribe_call_convention(engines):
    assert qwen._transcribe("transformers", "Qwen/Qwen3-ASR-1.7B", CLIPS, None) == \
        [("English", "Hello, world."), ("English", "Hello, world.")]
    source, kwargs = engines["asr_load"]
    assert source == "src:Qwen/Qwen3-ASR-1.7B"
    assert kwargs == {"dtype": "bf16", "device_map": "cuda:0", "max_inference_batch_size": 1,
                      "max_new_tokens": qwen.MAX_NEW_TOKENS}
    assert engines["asr"] == [(SR, SR, None), (SR, SR // 10, None)]
    # Budget by clip length (qwen-asr reads model.max_new_tokens on every generate).
    assert engines["asr_tokens"] == [qwen.token_budget(1), qwen.token_budget(0.1)]
    # A forced language is passed through and reported as-is.
    assert qwen._transcribe("transformers", "r", CLIPS[:1], "Japanese") == [("Japanese", "Hello, world.")]
    engines["free"].assert_called_with("transformers")


def test_mlx_transcribe_call_convention(engines):
    assert qwen._transcribe("mlx", "mlx-community/Qwen3-ASR-0.6B-8bit", CLIPS, None) == \
        [("Chinese", "你好。"), ("Chinese", "你好。")]
    source, length, kwargs = engines["mlx"][1]
    assert source == "src:mlx-community/Qwen3-ASR-0.6B-8bit" and length == SR // 10
    # Windows are <= 180 s and >= 0.1 s: one MLX chunk each, never zero-padded to 1 s.
    assert kwargs == {"language": None, "max_tokens": qwen.token_budget(0.1),
                      "chunk_duration": qwen.WINDOW_SECONDS + 1, "min_chunk_duration": qwen.MIN_WINDOW_SECONDS}
    assert qwen.MIN_WINDOW_SECONDS * SR <= SR // 10


def test_align_call_conventions(engines):
    jobs = [(CLIPS[0], "Hello, world.", "English")]
    assert qwen._align("transformers", "Qwen/Qwen3-ForcedAligner-0.6B", jobs) == \
        [[("Hello", 0.1, 0.4), ("world", 0.5, 0.9)]]
    assert engines["align_load"] == ("src:Qwen/Qwen3-ForcedAligner-0.6B", {"dtype": "bf16", "device_map": "cuda:0"})
    assert engines["align"] == [(SR, "Hello, world.", "English")]
    assert qwen._align("mlx", "m", [(CLIPS[0], "你好。", "Chinese")]) == [[("你", 0.0, 0.2), ("好", 0.2, 0.4)]]
    assert engines["mlx"][-1][2] == {"text": "你好。", "language": "Chinese"}


@pytest.mark.parametrize("engine", ["transformers", "mlx"])
def test_models_are_released_when_inference_fails(engines, engine):
    engines["fail"] = True
    with pytest.raises(RuntimeError):
        qwen._transcribe(engine, "r", CLIPS, None)
    engines["free"].assert_called_once_with(engine)
    with pytest.raises(RuntimeError):
        qwen._align(engine, "r", [(CLIPS[0], "Hi.", "English")])
    assert engines["free"].call_count == 2


def test_free_tolerates_missing_engine_library(monkeypatch):
    monkeypatch.setitem(sys.modules, "mlx", None)  # import mlx.core -> ImportError
    monkeypatch.setitem(sys.modules, "mlx.core", None)
    qwen._free("mlx")


@pytest.mark.parametrize("cuda,bf16,expected", [
    (True, True, ("cuda:0", "bfloat16")),
    (True, False, ("cuda:0", "float16")),
    (False, False, ("cpu", "float32")),
])
def test_torch_device_and_dtype(monkeypatch, cuda, bf16, expected):
    fake = types.ModuleType("torch")
    fake.bfloat16, fake.float16, fake.float32 = "bfloat16", "float16", "float32"
    fake.cuda = SimpleNamespace(is_available=lambda: cuda, is_bf16_supported=lambda: bf16)
    monkeypatch.setitem(sys.modules, "torch", fake)
    assert qwen._torch_device() == expected


# ------------------------------------------------------------------
# Token budget, forced wrong language, all probes unusable
# ------------------------------------------------------------------

def test_token_budget_scales_with_clip_length():
    assert qwen.token_budget(20) <= 256                            # a looping 20 s probe stops early
    assert qwen.token_budget(180) <= qwen.MAX_NEW_TOKENS == 2048   # full windows keep the old cap
    assert qwen.token_budget(3000) == qwen.MAX_NEW_TOKENS
    # Enough for very fast speech: ~8 chars/s Chinese is ~6 tokens/s, plus the language prefix.
    for seconds in (0.1, 5, 20, 60, 180):
        assert qwen.token_budget(seconds) >= 8 * seconds + 20


def test_forced_wrong_language_is_caught(pipeline):
    """Mini fix2_cs_en_forced: code-switched zh audio forced to en gave "Yeah, yeah, yeah." (rc=0)."""
    pipeline["language"] = "en"
    pipeline["asr"] = lambda a, b, language: ("Chinese,English", ZH) if language is None \
        else (language, "Yeah, yeah, yeah.")
    with pytest.raises(ValueError, match=r"0\.0-150\.\d+s is still degenerate after retrying \(only \d+ letters/digits, "
                                         r"while auto-detected probe clips.*\(English\) may not match the audio: try auto"):
        qwen.transcribe_audio("raw.wav", "raw.wav", 0, 200)
    calls = pipeline["calls"]["asr"]
    # Long window -> sparse -> lazy auto probes -> retry in <= 60 s windows -> error.
    assert calls[0][2] == "English" and calls[1][2] is None
    assert any(language == "English" and s <= qwen.RETRY_WINDOW_SECONDS for _, s, language in calls)


def test_forced_language_normal_speech_is_not_probed(pipeline):
    pipeline["language"] = "zh"
    pipeline["asr"] = lambda a, b, language: (language, ZH * max(1, int((b - a) // 10)))
    qwen.transcribe_audio("raw.wav", "raw.wav", 0, 200)
    assert all(language == "Chinese" for *_, language in pipeline["calls"]["asr"])  # no probes at all


def test_forced_language_silence_and_music_is_not_flagged(pipeline):
    # Sparse windows are probed, but probes of silence/music hear nothing, so nothing is flagged.
    pipeline["language"] = "zh"
    pipeline["asr"] = lambda a, b, language: ("", "") if language is None else (language, "" if b <= 60 else "我们。")
    result = qwen.transcribe_audio("raw.wav", "raw.wav", 0, 200)
    assert [segment["text"] for segment in result["segments"]] == ["我们。", "我们。"]


def test_forced_language_sparse_but_real_speech_passes(pipeline):
    # A few real words in a long window: probes hear about as much, so it is accepted.
    pipeline["language"] = "zh"
    pipeline["asr"] = lambda a, b, language: (("Chinese", "好的，谢谢大家。") if language is None
                                              else (language, "好的，谢谢大家。今天就到这里。"))
    result = qwen.transcribe_audio("raw.wav", "raw.wav", 0, 200)
    assert len(result["segments"]) == 2


def test_auto_all_probes_looping_reprobes_with_shorter_clips(pipeline):
    pipeline["language"] = "auto"

    def asr(a, b, language):
        if language is None:
            if b - a > qwen.REPROBE_SECONDS + 1:
                return "English", "Yeah, yeah. " * 100      # every 20 s probe loops
            return "Chinese", ZH                              # 10 s re-probes work
        return language, ZH * max(1, int((b - a) // 10))
    pipeline["asr"] = asr
    result = qwen.transcribe_audio("raw.wav", "raw.wav", 0, 200)
    reprobes = [s for _, s, language in pipeline["calls"]["asr"] if language is None and s <= qwen.REPROBE_SECONDS + 1]
    assert len(reprobes) > 3 and result["language"] == "zh"
    assert [language for *_, language in window_calls(pipeline)] == ["Chinese", "Chinese"]


def test_auto_all_probes_unusable_fails_instead_of_guessing(pipeline):
    pipeline["language"] = "auto"
    pipeline["asr"] = lambda a, b, language: ("English", "Yeah, yeah. " * 100) if language is None \
        else pytest.fail("must not transcribe without a language")
    with pytest.raises(ValueError, match="could not determine the language: every probe clip looped"):
        qwen.transcribe_audio("raw.wav", "raw.wav", 0, 200)
