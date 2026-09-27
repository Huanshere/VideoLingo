"""Regression tests for the backlog clean-up fixes (offline, no models, no network)."""
import pandas as pd
import pytest


# ------------------------------------------------------------------
# _6_gen_sub: punctuation-only subtitle lines (#459, #471)
# ------------------------------------------------------------------

def _words():
    return pd.DataFrame({
        "text": ["Hello", "world.", "How", "are", "you?"],
        "start": [0.0, 0.5, 2.0, 2.4, 2.8],
        "end": [0.4, 1.0, 2.3, 2.7, 3.2],
    })


@pytest.mark.parametrize("sentences,expected", [
    (["...", "Hello world.", "How are you?"], [(0.0, 0.0), (0.0, 1.0), (2.0, 3.2)]),
    (["Hello world.", "——", "How are you?"], [(0.0, 1.0), (1.0, 2.0), (2.0, 3.2)]),
    (["Hello world.", "How are you?", "!"], [(0.0, 1.0), (2.0, 3.2), (3.2, 3.2)]),
    (["Hello world.", "…", "。", "How are you?"], [(0.0, 1.0), (1.0, 2.0), (2.0, 2.0), (2.0, 3.2)]),
])
def test_punctuation_only_lines_get_a_timestamp(sentences, expected):
    from core._6_gen_sub import get_sentence_timestamps

    stamps = get_sentence_timestamps(_words(), pd.DataFrame({"Source": sentences}))

    assert stamps == expected
    assert all(start <= end for start, end in stamps)


def test_unmatched_sentence_still_raises():
    from core._6_gen_sub import get_sentence_timestamps

    with pytest.raises(ValueError):
        get_sentence_timestamps(_words(), pd.DataFrame({"Source": ["Hello world.", "Something else"]}))


# ------------------------------------------------------------------
# _5_split_sub: re-merged translation follows the target script (#359)
# ------------------------------------------------------------------

@pytest.mark.parametrize("source_language,parts,expected", [
    ("en", ["今天我们来聊一聊", "人工智能的未来"], "今天我们来聊一聊人工智能的未来"),
    ("en", ["我们用 Python", "写了 3 个脚本"], "我们用 Python写了 3 个脚本"),
    ("zh", ["Today we talk about", "the future of AI"], "Today we talk about the future of AI"),
    ("ja", ["It shipped in 2024", "5 people built it"], "It shipped in 2024 5 people built it"),
    ("en", ["오늘은 인공지능의", "미래를 이야기합니다"], "오늘은 인공지능의 미래를 이야기합니다"),
])
def test_remerged_translation_uses_target_script_joiner(monkeypatch, source_language, parts, expected):
    import core._5_split_sub as split_sub

    align = [{f"target_part_{i + 1}": part} for i, part in enumerate(parts)]
    monkeypatch.setattr(split_sub, "ask_gpt", lambda *args, **kwargs: {"align": align})
    monkeypatch.setattr(split_sub, "load_key", lambda key: source_language if key.startswith("whisper") else None)

    _, tr_parts, remerged = split_sub.align_subs("src", "tr", "src part 1\nsrc part 2")

    assert tr_parts == parts
    assert remerged == expected


# ------------------------------------------------------------------
# ask_gpt: a local LLM needs no API key (#415, #540)
# ------------------------------------------------------------------

def _ask_gpt_module():
    import sys
    import core.utils  # noqa: F401  (core.utils.ask_gpt the attribute is the function)
    return sys.modules["core.utils.ask_gpt"]


@pytest.mark.parametrize("base_url,local", [
    ("http://localhost:11434/v1", True),
    ("http://127.0.0.1:1234", True),
    ("http://192.168.1.20:8000/v1", True),
    ("http://host.docker.internal:11434/v1", True),
    ("http://[::1]:8080/v1", True),
    ("0.0.0.0:8000", True),
    ("https://api.openai.com/v1", False),
    ("https://localhost.example.com/v1", False),
    ("https://8.8.8.8/v1", False),
    ("", False),
])
def test_is_local_endpoint(base_url, local):
    assert _ask_gpt_module().is_local_endpoint(base_url) is local


@pytest.mark.parametrize("key,base_url,expected", [
    ("sk-test", "https://api.openai.com/v1", "sk-test"),
    ("sk-test", "http://localhost:11434/v1", "sk-test"),
    ("", "http://localhost:11434/v1", "not-needed"),
    (None, "http://127.0.0.1:1234/v1", "not-needed"),
])
def test_get_api_key(monkeypatch, key, base_url, expected):
    module = _ask_gpt_module()
    monkeypatch.setattr(module, "load_key", {"api.key": key, "api.base_url": base_url}.get)
    assert module.get_api_key() == expected


def test_empty_key_for_a_hosted_endpoint_is_still_an_error(monkeypatch):
    module = _ask_gpt_module()
    monkeypatch.setattr(module, "load_key", {"api.key": "", "api.base_url": "https://api.openai.com/v1"}.get)
    with pytest.raises(ValueError, match="API key is not set"):
        module.get_api_key()


# ------------------------------------------------------------------
# sidebar: recognition language dropdown (#395, #264, #280, #394, #408, #475)
# ------------------------------------------------------------------

def test_recognition_languages_cover_every_qwen_language():
    from core.asr_backend.qwen_asr_local import ISO_TO_QWEN
    from core.st_utils.sidebar_setting import LANGUAGE_LABELS, recognition_languages

    langs = recognition_languages("en")

    assert list(langs.values())[:9] == ["auto", "en", "zh", "es", "ru", "fr", "de", "it", "ja"]
    assert set(langs.values()) == {"auto", *ISO_TO_QWEN}
    assert len(langs) == len(ISO_TO_QWEN) + 1
    assert set(LANGUAGE_LABELS) == set(ISO_TO_QWEN)


@pytest.mark.parametrize("configured", ["uk", "he", None])
def test_hand_configured_language_does_not_break_the_dropdown(configured):
    from core.st_utils.sidebar_setting import recognition_languages

    langs = recognition_languages(configured)

    assert list(langs.values()).index(configured) == len(langs) - 1


# ------------------------------------------------------------------
# core.utils: a missing dependency is reported by name (#513)
# ------------------------------------------------------------------

def test_core_utils_reports_the_import_that_failed():
    import subprocess
    import sys
    from pathlib import Path

    code = (
        "import sys\n"
        "sys.modules['json_repair'] = None\n"  # makes `import json_repair` raise ImportError
        "import core.utils\n"                  # still importable, as the installer expects
        "try:\n"
        "    from core.utils import *\n"
        "except ImportError as e:\n"
        "    print('ImportError:', e)\n"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                            cwd=Path(__file__).resolve().parents[1])

    assert result.returncode == 0, result.stderr
    assert "ImportError:" in result.stdout
    assert "json_repair" in result.stdout


def test_core_utils_unknown_attribute_is_still_an_attribute_error():
    import core.utils

    with pytest.raises(AttributeError):
        core.utils.does_not_exist


# ------------------------------------------------------------------
# _4_2_translate: a first sentence longer than the chunk size (replaces PR #479)
# ------------------------------------------------------------------

def test_split_chunks_has_no_empty_chunk(tmp_path, monkeypatch):
    import core._4_2_translate as translate

    sentences = ["x" * 50, "short one", "short two", "y" * 50, "short three"]
    source = tmp_path / "split_by_meaning.txt"
    source.write_text("\n".join(sentences), encoding="utf-8")
    monkeypatch.setattr(translate, "_3_2_SPLIT_BY_MEANING", str(source))

    chunks = translate.split_chunks_by_chars(chunk_size=30, max_i=10)

    assert all(chunk.strip() for chunk in chunks)
    assert "\n".join(chunks).split("\n") == sentences


# ------------------------------------------------------------------
# _9_refer_audio: the skip check looks at the reference directory
# ------------------------------------------------------------------

def _refer_audio(monkeypatch, tmp_path):
    import numpy as np
    import core._9_refer_audio as refer

    refers, segs = tmp_path / "refers", tmp_path / "segs"
    segs.mkdir()
    monkeypatch.setattr(refer, "_AUDIO_REFERS_DIR", str(refers))
    monkeypatch.setattr(refer, "_AUDIO_SEGS_DIR", str(segs))
    monkeypatch.setattr(refer, "find_spec", lambda name: None)
    monkeypatch.setattr(refer.pd, "read_excel", lambda path: pd.DataFrame(
        {"number": [1, 2], "start_time": ["00:00:00,000", "00:00:01,000"], "end_time": ["00:00:01,000", "00:00:02,000"]}))
    monkeypatch.setattr(refer.sf, "read", lambda path: (np.zeros(32000, dtype="float32"), 16000))
    return refer, refers, segs


def test_refer_audio_is_extracted_even_when_dub_segments_exist(monkeypatch, tmp_path):
    refer, refers, segs = _refer_audio(monkeypatch, tmp_path)
    (segs / "1.wav").write_bytes(b"left over from an earlier dubbing run")

    refer.extract_refer_audio_main()

    assert sorted(path.name for path in refers.iterdir()) == ["1.wav", "2.wav"]


def test_refer_audio_is_skipped_when_references_exist(monkeypatch, tmp_path):
    refer, refers, _ = _refer_audio(monkeypatch, tmp_path)
    refers.mkdir()
    (refers / "1.wav").write_bytes(b"existing")

    refer.extract_refer_audio_main()

    assert [path.name for path in refers.iterdir()] == ["1.wav"]


# ------------------------------------------------------------------
# tts_settings: follow-ups to PR #613
# ------------------------------------------------------------------

def test_configured_keys_accepts_a_non_string_key():
    from core.st_utils.tts_settings import configured_keys

    config = {"azure_tts.api_key": 1234567890, "openai_tts.api_key": None,
              "fish_tts.api_key": "YOUR_302_API_KEY", "f5tts.302_api": ""}

    assert configured_keys("302.ai", "openai_tts", config.get) == ("1234567890", False)


# ------------------------------------------------------------------
# ask_gpt: replies of reasoning models and chatty models (#478, #490, #422)
# ------------------------------------------------------------------

@pytest.mark.parametrize("content,expected", [
    ('{"message": "success"}', {"message": "success"}),
    ('```json\n{"message": "success"}\n```', {"message": "success"}),
    ('<think>\nThe user wants {"message": "draft"}.\n</think>\n\n{"message": "success"}', {"message": "success"}),
    ('<think>plan</think>\n```json\n{"message": "success"}\n```', {"message": "success"}),
    ('reasoning without the opening tag {"a": 1}</think>{"message": "success"}', {"message": "success"}),
    ('Here is an example {"message": "draft"} and the answer:\n```json\n{"message": "success"}\n```\nHope it helps {ok}',
     {"message": "success"}),
    ('```json\n{"message": "draft"}\n```\nCorrected:\n```json\n{"message": "success"}\n```', {"message": "success"}),
    ('Sure! {"message": "success"}', {"message": "success"}),
    ('{"message": "success",}', {"message": "success"}),
    ('{"1": {"origin": "a ```code``` b", "direct": "甲"}}', {"1": {"origin": "a ```code``` b", "direct": "甲"}}),
])
def test_parse_json_response(content, expected):
    assert _ask_gpt_module().parse_json_response(content) == expected


@pytest.mark.parametrize("content", ["", None, "I cannot help with that.", "<think>still thinking", "[1, 2, 3]", '"success"'])
def test_parse_json_response_rejects_a_reply_without_an_object(content):
    with pytest.raises(ValueError, match="not a JSON object"):
        _ask_gpt_module().parse_json_response(content)


@pytest.mark.parametrize("base_url,expected", [
    ("https://api.openai.com/v1", "https://api.openai.com/v1"),
    ("https://api.openai.com", "https://api.openai.com/v1"),
    ("https://api.openai.com/", "https://api.openai.com/v1"),
    ("https://api.openai.com/v1/", "https://api.openai.com/v1"),
    ("https://api.openai.com/v1/chat/completions", "https://api.openai.com/v1"),
    ("https://api.openai.com/v1/chat/completions/", "https://api.openai.com/v1"),
    ("http://localhost:11434/v1/chat/completions", "http://localhost:11434/v1"),
    (" https://api.deepseek.com ", "https://api.deepseek.com/v1"),
    ("https://ark.cn-beijing.volces.com/api/v3/chat/completions", "https://ark.cn-beijing.volces.com/api/v3"),
])
def test_normalize_base_url(base_url, expected):
    assert _ask_gpt_module().normalize_base_url(base_url) == expected


def test_normalize_base_url_keeps_other_api_versions():
    assert _ask_gpt_module().normalize_base_url("https://open.bigmodel.cn/api/paas/v4/") == "https://open.bigmodel.cn/api/paas/v4"


# ------------------------------------------------------------------
# sidebar: API check reports the real error (#465, #405, #390, #440)
# ------------------------------------------------------------------

class _FakeCompletions:
    def __init__(self, outcome):
        self.outcome, self.calls = outcome, 0

    def create(self, **params):
        self.calls += 1
        if isinstance(self.outcome, Exception):
            raise self.outcome
        from types import SimpleNamespace
        message = SimpleNamespace(content=self.outcome)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def _check_api(monkeypatch, tmp_path, outcome, key="sk-test"):
    from types import SimpleNamespace
    import core.st_utils.sidebar_setting as sidebar

    module = _ask_gpt_module()
    completions = _FakeCompletions(outcome)
    config = {"api.key": key, "api.base_url": "https://api.example.com/v1/chat/completions",
              "api.model": "test-model", "api.llm_support_json": False}
    seen = {}

    def fake_openai(api_key, base_url):
        seen.update(api_key=api_key, base_url=base_url)
        return SimpleNamespace(chat=SimpleNamespace(completions=completions))

    monkeypatch.setattr(module, "load_key", config.get)
    monkeypatch.setattr(module, "OpenAI", fake_openai)
    monkeypatch.setattr(module, "GPT_LOG_FOLDER", str(tmp_path))
    return sidebar.check_api(), completions, seen


def test_check_api_success(monkeypatch, tmp_path):
    result, completions, seen = _check_api(monkeypatch, tmp_path, '<think>ok</think>{"message": "success"}')

    assert result == (True, "")
    assert seen == {"api_key": "sk-test", "base_url": "https://api.example.com/v1"}
    assert completions.calls == 1


def test_check_api_reports_the_error_without_retrying(monkeypatch, tmp_path):
    result, completions, _ = _check_api(monkeypatch, tmp_path, ConnectionError("model `test-model` not found"))

    assert result == (False, "ConnectionError: model `test-model` not found")
    assert completions.calls == 1


def test_check_api_is_not_answered_from_the_cache(monkeypatch, tmp_path):
    import core.st_utils.sidebar_setting as sidebar

    _check_api(monkeypatch, tmp_path, '{"message": "success"}')
    monkeypatch.setattr(sidebar.time, "time", lambda: 1.0)
    result, completions, _ = _check_api(monkeypatch, tmp_path, ConnectionError("key revoked"))

    assert result[0] is False
    assert completions.calls == 1


def test_check_api_without_key(monkeypatch, tmp_path):
    result, completions, _ = _check_api(monkeypatch, tmp_path, '{"message": "success"}', key="")

    assert result == (False, "ValueError: API key is not set")
    assert completions.calls == 0

