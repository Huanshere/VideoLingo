"""Offline checks for the Qwen3-ASR + ForcedAligner backend (no model downloads, no inference)."""
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


@pytest.fixture
def pipeline(monkeypatch):
    """Mock config, audio decoding and both engines; return the recorded calls."""
    state = {"language": "en", "texts": None, "calls": {}}
    audio = {"raw.wav": np.full(200 * SR, 0.5, dtype=np.float32),
             "vocal.mp3": np.full(200 * SR, 0.25, dtype=np.float32)}
    audio["raw.wav"][150 * SR:151 * SR] = 0  # first window cut at 150-151 s

    monkeypatch.setattr(qwen, "resolve_engine", lambda requested=None: "transformers")
    monkeypatch.setattr(qwen, "model_size", lambda requested=None: "0.6b")
    monkeypatch.setattr(qwen, "load_key", lambda key: {"whisper.language": state["language"]}[key])
    monkeypatch.setattr(qwen, "load_audio_segment", lambda path, start, end: audio[path])

    def transcribe(engine, repo_id, clips, language):
        state["calls"]["transcribe"] = (engine, repo_id, [len(c) for c in clips], language)
        return state["texts"](language)

    def align(engine, repo_id, jobs):
        state["calls"]["align"] = (engine, repo_id, [(float(c[0]), text, lang) for c, text, lang in jobs])
        return [[(tok, 0.5 + i, 1.0 + i) for i, tok in enumerate(text.rstrip(".").replace(",", "").split())]
                for _, text, _ in jobs]

    monkeypatch.setattr(qwen, "_transcribe", transcribe)
    monkeypatch.setattr(qwen, "_align", align)
    return state


def test_transcribe_audio_structure_offsets_and_cache_validity(pipeline):
    pipeline["texts"] = lambda language: [(language, "Hello, world."), (language, "Bye now.")]
    result = qwen.transcribe_audio("raw.wav", "vocal.mp3", 60, 260)

    engine, repo, lengths, language = pipeline["calls"]["transcribe"]
    assert (engine, repo, language) == ("transformers", "Qwen/Qwen3-ASR-0.6B", "English")
    assert len(lengths) == 2 and sum(lengths) == 200 * SR and max(lengths) <= 180 * SR
    engine, repo, jobs = pipeline["calls"]["align"]
    assert repo == "Qwen/Qwen3-ForcedAligner-0.6B"
    # Alignment runs on the vocal track with the forced language.
    assert [(c, lang) for c, _, lang in jobs] == [(0.25, "English"), (0.25, "English")]

    assert result["language"] == "en"
    first, second = result["segments"]
    assert first["text"] == "Hello, world." and [w["word"] for w in first["words"]] == ["Hello,", "world."]
    assert first["words"][0] == {"word": "Hello,", "start": 60.5, "end": 61.0}
    window_start = 60 + lengths[0] / SR
    assert second["words"][0]["start"] == pytest.approx(window_start + 0.5, abs=1e-3)
    assert first["start"] == first["words"][0]["start"] and second["end"] == second["words"][-1]["end"]
    assert cache.valid_result(result)


def test_auto_language_votes_and_skips_empty_windows(pipeline):
    pipeline["language"] = "auto"
    pipeline["texts"] = lambda language: [("Chinese,English", "你好。"), ("English", "")]
    result = qwen.transcribe_audio("raw.wav", "raw.wav", 0, 200)
    assert pipeline["calls"]["transcribe"][3] is None
    # Only the non-empty window is aligned, with its primary language; raw doubles as vocal.
    assert pipeline["calls"]["align"][2] == [(0.5, "你好。", "Chinese")]
    assert result["language"] == "zh" and len(result["segments"]) == 1


def test_auto_language_falls_back_to_majority_for_unlabelled_windows(pipeline):
    pipeline["language"] = "auto"
    pipeline["texts"] = lambda language: [("English", "One."), ("", "Two.")]
    result = qwen.transcribe_audio("raw.wav", "raw.wav", 0, 200)
    assert [lang for _, _, lang in pipeline["calls"]["align"][2]] == ["English", "English"]
    assert result["language"] == "en"


def test_undetectable_language_asks_user_to_set_it(pipeline):
    pipeline["language"] = "auto"
    pipeline["texts"] = lambda language: [("", "???"), ("", "")]
    with pytest.raises(ValueError, match="set the recognition language"):
        qwen.transcribe_audio("raw.wav", "raw.wav", 0, 200)


def test_silence_returns_empty_segments_without_loading_aligner(pipeline):
    pipeline["language"] = "auto"
    pipeline["texts"] = lambda language: [("", ""), ("", "")]
    result = qwen.transcribe_audio("raw.wav", "raw.wav", 0, 200)
    assert result == {"language": None, "segments": []}
    assert "align" not in pipeline["calls"]
