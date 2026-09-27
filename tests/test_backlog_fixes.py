"""Regression tests for the backlog clean-up fixes (offline, no models, no network)."""
import os

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



# ------------------------------------------------------------------
# split_by_mark: long videos are tokenized in batches (#238)
# ------------------------------------------------------------------

def test_batch_words_stays_below_the_byte_limit_and_cuts_after_sentences():
    from core.spacy_utils.split_by_mark import batch_words

    words = [word for i in range(300) for word in ("これは", "とても", "長い", f"文{i}", "です。")]

    batches = batch_words(words, max_bytes=1000)

    assert [word for batch in batches for word in batch] == words
    assert len(batches) > 1
    assert all(sum(len(word.encode("utf-8")) + 1 for word in batch) <= 1000 for batch in batches)
    assert all(batch[-1].endswith("。") for batch in batches)


def test_batch_words_without_punctuation_and_short_input():
    from core.spacy_utils.split_by_mark import batch_words

    words = ["word"] * 1000

    assert batch_words(["short", "text."]) == [["short", "text."]]
    assert batch_words([]) == []
    batches = batch_words(words, max_bytes=100)
    assert [word for batch in batches for word in batch] == words
    assert all(len(batch) == 20 for batch in batches)


def test_split_by_mark_handles_text_longer_than_the_tokenizer_limit(tmp_path, monkeypatch):
    import sys
    import spacy
    import core.spacy_utils.split_by_mark  # noqa: F401  (the package re-exports the function under this name)
    module = sys.modules["core.spacy_utils.split_by_mark"]

    nlp = spacy.blank("en")
    nlp.add_pipe("sentencizer")
    seen = []

    def limited_nlp(text):
        seen.append(len(text.encode("utf-8")))
        assert seen[-1] <= 49149
        return nlp(text)

    words = [word for i in range(6000) for word in ("This", "is", "sentence", "number", f"{i}.")]
    output = tmp_path / "split_by_mark.txt"
    monkeypatch.setattr(module, "SPLIT_BY_MARK_FILE", str(output))
    monkeypatch.setattr(module, "load_key", lambda key: "en")
    monkeypatch.setattr(module.pd, "read_excel", lambda path: pd.DataFrame({"text": words}))

    module.split_by_mark(limited_nlp)

    lines = output.read_text(encoding="utf-8").splitlines()
    assert len(seen) > 1
    assert lines == [f"This is sentence number {i}." for i in range(6000)]


# ------------------------------------------------------------------
# _10_gen_audio: dubbing that does not fit is sped up to the limit, then truncated
# (#436, #453, #351, #536)
# ------------------------------------------------------------------

def _chunk(real_durs, tol_dur=2.0, tolerance=0.0, gap=0.0):
    count = len(real_durs)
    return pd.DataFrame({"real_dur": real_durs, "tol_dur": [tol_dur] * count,
                         "tolerance": [tolerance] * count, "gap": [gap] * count})


@pytest.mark.parametrize("chunk,expected", [
    (_chunk([1.0, 1.0]), (1.0, True)),                       # fits as it is
    (_chunk([2.2, 2.2]), (1.128, True)),                     # a little faster
    (_chunk([5.0, 5.0]), (1.4, False)),                      # used to be 2.564
    (_chunk([87.6], tol_dur=0.2), (1.4, False)),             # used to be atempo=876
    (_chunk([1.0], tol_dur=0.1), (1.4, False)),              # used to divide by zero
    (_chunk([1.0], tol_dur=0.05), (1.4, False)),             # used to be negative
])
def test_speed_factor_is_clamped(chunk, expected):
    from core._10_gen_audio import process_chunk

    assert process_chunk(chunk, accept=1.2, min_speed=1.0, max_speed=1.4) == expected


def _dub_tasks(monkeypatch, tmp_path, durations, lines):
    """Two rows that share one 4 second chunk; adjust_audio_speed writes real wav files."""
    from pydub import AudioSegment
    from pydub.generators import Sine
    from core import _10_gen_audio as audio

    durations = dict(zip(("1_0", "2_0", "2_1"), durations))
    config = {"speed_factor.accept": 1.2, "speed_factor.min": 1.0, "speed_factor.max": 1.4}

    def fake_speed(temp_file, output_file, speed_factor):
        name = os.path.basename(output_file)[:-len(".wav")]
        Sine(440).to_audio_segment(duration=int(durations[name] / speed_factor * 1000)).export(output_file, format="wav")

    monkeypatch.setattr(audio, "load_key", config.get)
    monkeypatch.setattr(audio, "adjust_audio_speed", fake_speed)
    monkeypatch.setattr(audio, "get_audio_duration", lambda path: len(AudioSegment.from_wav(path)) / 1000)
    monkeypatch.setattr(audio, "OUTPUT_FILE_TEMPLATE", str(tmp_path / "{}.wav"))
    monkeypatch.setattr(audio, "TRUNCATED_LOG", str(tmp_path / "log" / "dub_truncated.json"))
    tasks = pd.DataFrame({
        "number": [1, 2], "cut_off": [0, 1], "tol_dur": [2.0, 2.0], "tolerance": [0.0, 0.0], "gap": [0.0, 0.0],
        "real_dur": [durations["1_0"], durations["2_0"] + durations["2_1"]],
        "start_time": ["00:00:10.000", "00:00:12.000"], "end_time": ["00:00:12.000", "00:00:14.000"],
        "lines": [lines[:1], lines[1:]],
    })
    return audio, tasks


def test_overlong_dubbing_is_truncated_and_logged(monkeypatch, tmp_path):
    import json
    from pydub import AudioSegment

    audio, tasks = _dub_tasks(monkeypatch, tmp_path, (2.8, 2.1, 2.8), ["first", "second", "third"])

    result = audio.merge_chunks(tasks)

    # at the 1.4 limit: 2.0s + 1.5s + 2.0s in a 4 second chunk
    assert result.at[0, "new_sub_times"] == [[10.0, 12.0]]
    assert result.at[1, "new_sub_times"] == [[12.0, 13.5], [13.5, 14.0]]
    assert len(AudioSegment.from_wav(tmp_path / "2_1.wav")) == 500
    assert len(AudioSegment.from_wav(tmp_path / "2_0.wav")) == 1500
    log = json.loads((tmp_path / "log" / "dub_truncated.json").read_text(encoding="utf-8"))
    assert log == [{"number": 2, "line": "third", "spoken_seconds": 2.0, "kept_seconds": 0.5, "speed_factor": 1.4}]


def test_line_that_starts_after_the_chunk_end_becomes_silence(monkeypatch, tmp_path):
    import json
    from pydub import AudioSegment

    audio, tasks = _dub_tasks(monkeypatch, tmp_path, (4.2, 2.8, 1.4), ["first", "second", "third"])

    result = audio.merge_chunks(tasks)

    # 3.0s + 2.0s + 1.0s: the second line is cut to 1s, the third has no room at all
    assert result.at[0, "new_sub_times"] == [[10.0, 13.0]]
    assert result.at[1, "new_sub_times"] == [[13.0, 14.0], [14.0, 14.0]]
    assert len(AudioSegment.from_wav(tmp_path / "2_1.wav")) == 10
    assert AudioSegment.from_wav(tmp_path / "2_1.wav").rms == 0
    log = json.loads((tmp_path / "log" / "dub_truncated.json").read_text(encoding="utf-8"))
    assert [(item["line"], item["kept_seconds"]) for item in log] == [("second", 1.0), ("third", 0.0)]


def test_dubbing_that_fits_leaves_no_truncation_log(monkeypatch, tmp_path):
    audio, tasks = _dub_tasks(monkeypatch, tmp_path, (1.5, 1.0, 1.0), ["first", "second", "third"])
    log = tmp_path / "log" / "dub_truncated.json"
    log.parent.mkdir()
    log.write_text("[]", encoding="utf-8")  # left by an earlier run

    result = audio.merge_chunks(tasks)

    assert result.at[1, "new_sub_times"][-1][1] <= 14.0
    assert not log.exists()


def test_abnormal_duration_after_speed_change_is_trimmed(monkeypatch, tmp_path):
    from pydub import AudioSegment
    from pydub.generators import Sine
    from core import _10_gen_audio as audio

    source, output = tmp_path / "in.wav", tmp_path / "out.wav"
    Sine(440).to_audio_segment(duration=4000).export(source, format="wav")

    def fake_ffmpeg(cmd, **kwargs):  # an ffmpeg that ignores atempo
        Sine(440).to_audio_segment(duration=4000).export(cmd[-1], format="wav")

    monkeypatch.setattr(audio.subprocess, "run", fake_ffmpeg)
    monkeypatch.setattr(audio, "get_audio_duration", lambda path: len(AudioSegment.from_wav(path)) / 1000)

    audio.adjust_audio_speed(str(source), str(output), 1.25)

    assert len(AudioSegment.from_wav(output)) == 3200


# ------------------------------------------------------------------
# _3_2_split_meaning: tolerant of the split reply, mechanical fallback (#340)
# ------------------------------------------------------------------

@pytest.mark.parametrize("response,expected", [
    ({"split1": "a b[br]c d", "split2": "a[br]b c d", "choice": "2"}, "a[br]b c d"),
    ({"split1": "a b[br]c d", "split2": "a[br]b c d", "choice": 1}, "a b[br]c d"),
    ({"split1": "a b[br]c d", "split2": "a[br]b c d", "choice": "split2"}, "a[br]b c d"),
    ({"split1": "a b[br]c d", "split2": "a[br]b c d", "choice": "1 or 2"}, "a b[br]c d"),
    ({"split1": "a b[br]c d", "split2": "a[br]b c d"}, "a b[br]c d"),
    ({"split1": "a b<br>c d", "choice": "1"}, "a b[br]c d"),
    ({"split1": "a b <br/> c d", "choice": "1"}, "a b [br] c d"),
    ({"split1": "a b[BR]c d", "choice": "1"}, "a b[br]c d"),
    ({"split1": "a b c d", "split2": "a b<BR />c d", "choice": "1"}, "a b[br]c d"),
    ({"split1": "a b c d[br]", "split2": "a b c d", "choice": "1"}, None),
    ({"choice": "3"}, None),
])
def test_pick_split(response, expected):
    from core._3_2_split_meaning import pick_split

    assert pick_split(response) == expected


def _split_meaning(monkeypatch, language, ask_gpt):
    import core._3_2_split_meaning as module

    monkeypatch.setattr(module, "get_split_prompt", lambda *args: "prompt")
    monkeypatch.setattr(module, "get_source_language", lambda: language)
    monkeypatch.setattr(module, "load_key", lambda key: language)
    monkeypatch.setattr(module, "ask_gpt", ask_gpt)
    return module


def test_split_sentence_accepts_html_br_and_missing_choice(monkeypatch):
    sentence = "This is the first half of the sentence, and this is the second half of it."
    reply = {"split1": "This is the first half of the sentence,<br>and this is the second half of it."}
    module = _split_meaning(monkeypatch, "en", lambda *args, valid_def, **kwargs: reply if valid_def(reply)["status"] == "success" else None)

    assert module.split_sentence(sentence, 2) == \
        "This is the first half of the sentence,\n and this is the second half of it."


@pytest.mark.parametrize("language,sentence,num_parts,expected", [
    ("en", "This is the first half of the sentence, and this is the second half of it.", 2,
     ["This is the first half of the sentence,", "and this is the second half of it."]),
    ("en", "one two three four five six seven eight nine ten eleven twelve", 3,
     ["one two three four", "five six seven eight", "nine ten eleven twelve"]),
    ("zh", "今天我们来聊一聊人工智能的未来，以及它会怎样改变每个人的生活", 2,
     ["今天我们来聊一聊人工智能的未来，", "以及它会怎样改变每个人的生活"]),
    ("zh", "今天我们来聊一聊人工智能的未来以及它会怎样改变每个人的生活", 2,
     ["今天我们来聊一聊人工智能的未", "来以及它会怎样改变每个人的生活"]),
    ("en", "Supercalifragilisticexpialidocious", 2, ["Supercalifragilisticexpialidocious"]),
])
def test_split_falls_back_to_a_mechanical_split(monkeypatch, language, sentence, num_parts, expected):
    def failing_ask_gpt(*args, **kwargs):
        raise ValueError("❎ API response error: Split failed, no [br] found")

    module = _split_meaning(monkeypatch, language, failing_ask_gpt)

    result = module.split_sentence(sentence, num_parts).split("\n")

    assert result == expected
    assert "".join(result).replace(" ", "") == sentence.replace(" ", "")


def test_split_does_not_swallow_a_stop_request(monkeypatch):
    from core.task_runner import StopTask

    def stopped(*args, **kwargs):
        raise StopTask()

    module = _split_meaning(monkeypatch, "en", stopped)

    with pytest.raises(StopTask):
        module.split_sentence("some long sentence that was being split", 2)


# ------------------------------------------------------------------
# translate_lines: extra keys, and a polish step that fails (#433)
# ------------------------------------------------------------------

def _translate_lines(monkeypatch, replies, reflect=True):
    import core.translate_lines as module

    calls = []

    def fake_ask_gpt(prompt, resp_type=None, valid_def=None, log_title="default"):
        calls.append(log_title)
        reply = replies[log_title]
        if isinstance(reply, Exception):
            raise reply
        check = valid_def(reply)
        if check["status"] != "success":
            raise ValueError(check["message"])
        return reply

    monkeypatch.setattr(module, "ask_gpt", fake_ask_gpt)
    monkeypatch.setattr(module, "load_key", lambda key: reflect)
    monkeypatch.setattr(module, "check_cancel", lambda: None)
    monkeypatch.setattr(module, "generate_shared_prompt", lambda *args: "shared")
    monkeypatch.setattr(module, "get_prompt_faithfulness", lambda *args: "faith")
    monkeypatch.setattr(module, "get_prompt_expressiveness", lambda *args: "express")
    return module, calls


FAITH = {"1": {"origin": "Hello.", "direct": "你好。"}, "2": {"origin": "Bye.", "direct": "再见。"}}


def test_translation_ignores_keys_the_model_added(monkeypatch):
    module, _ = _translate_lines(monkeypatch, {
        "translate_faithfulness": {**FAITH, "note": "two lines translated"},
        "translate_expressiveness": {"analysis": "fine", "1": {"free": "你好呀。"}, "2": {"free": "回头见。"}},
    })

    assert module.translate_lines("Hello.\nBye.", None, None, None, None) == ("你好呀。\n回头见。", "Hello.\nBye.")


def test_failed_polish_step_falls_back_to_the_direct_translation(monkeypatch):
    module, calls = _translate_lines(monkeypatch, {
        "translate_faithfulness": FAITH,
        "translate_expressiveness": {"1": {"free": "你好呀。"}, "2": "回头见。"},
    })

    assert module.translate_lines("Hello.\nBye.", None, None, None, None) == ("你好。\n再见。", "Hello.\nBye.")
    assert calls == ["translate_faithfulness", "translate_expressiveness"]


def test_failed_faithful_translation_is_still_an_error(monkeypatch):
    module, _ = _translate_lines(monkeypatch, {"translate_faithfulness": {"1": FAITH["1"]}})

    with pytest.raises(ValueError, match="Missing required key"):
        module.translate_lines("Hello.\nBye.", None, None, None, None)


# ------------------------------------------------------------------
# C6: a subtitle line is split on both sides or not at all (#369, #339)
# ------------------------------------------------------------------

def _split_sub(monkeypatch, split, align, max_length=20):
    import core._5_split_sub as module

    def fake_ask_gpt(prompt, resp_type=None, valid_def=None, log_title="default"):
        reply = align(prompt) if callable(align) else align
        if isinstance(reply, Exception):
            raise reply
        check = valid_def(reply)
        if check["status"] != "success":
            raise ValueError(check["message"])
        return reply

    settings = {"subtitle": {"max_length": max_length, "target_multiplier": 1.2}, "max_workers": 2}
    monkeypatch.setattr(module, "load_key", lambda key: settings[key])
    monkeypatch.setattr(module, "split_sentence", lambda sentence, num_parts: split(sentence) if callable(split) else split)
    monkeypatch.setattr(module, "get_align_prompt", lambda src, tr, part: tr)
    monkeypatch.setattr(module, "ask_gpt", fake_ask_gpt)
    return module


LONG_SRC = "this is a long source line that has to be split"
LONG_TR = "这是一行需要被切分的很长的译文字幕内容"


def test_split_sub_splits_both_sides(monkeypatch):
    module = _split_sub(
        monkeypatch,
        split="this is a long source line\nthat has to be split",
        align={"align": [{"target_part_1": "这是一行需要被切分的"}, {"target_part_2": "很长的译文字幕内容"}]},
    )

    src, tr, remerged = module.split_align_subs(["short", LONG_SRC], ["短", LONG_TR])

    assert src == ["short", "this is a long source line", "that has to be split"]
    assert tr == ["短", "这是一行需要被切分的", "很长的译文字幕内容"]
    assert remerged == ["短", "这是一行需要被切分的很长的译文字幕内容"]


@pytest.mark.parametrize("align", [
    {"align": [{"target_part_1": "这是"}, {"target_part_2": "一行"}, {"target_part_3": "译文"}]},
    {"align": [{"target_part_1": "这是一行需要被切分的很长的译文字幕内容"}, {"target_part_2": " "}]},
    {"align": [{"target_part_1": "这是一行"}, {"part_2": "译文"}]},
    {"align": "这是一行"},
    RuntimeError("connection reset"),
])
def test_split_sub_keeps_the_line_when_the_parts_do_not_match(monkeypatch, align):
    module = _split_sub(monkeypatch, split="this is a long source line\nthat has to be split", align=align)

    src, tr, remerged = module.split_align_subs(["short", LONG_SRC], ["短", LONG_TR])

    assert src == ["short", LONG_SRC]
    assert tr == ["短", LONG_TR]
    assert remerged == ["短", LONG_TR]


def test_split_sub_keeps_the_line_when_the_source_has_one_part(monkeypatch):
    module = _split_sub(
        monkeypatch,
        split=LONG_SRC,
        align={"align": [{"target_part_1": "这是一行"}, {"target_part_2": "译文"}]},
    )

    src, tr, _ = module.split_align_subs([LONG_SRC], [LONG_TR])

    assert (src, tr) == ([LONG_SRC], [LONG_TR])


def test_split_sub_stops_when_the_task_is_cancelled(monkeypatch):
    from core.task_runner import StopTask

    module = _split_sub(monkeypatch, split="this is a long source line\nthat has to be split", align=StopTask())

    with pytest.raises(StopTask):
        module.split_align_subs([LONG_SRC], [LONG_TR])


def test_split_sub_main_writes_lines_of_equal_length(monkeypatch, tmp_path):
    def align(prompt):
        if prompt == LONG_TR:
            return {"align": [{"target_part_1": "这是"}, {"target_part_2": "一行"}, {"target_part_3": "译文"}]}
        return {"align": [{"target_part_1": "第二行需要切分的"}, {"target_part_2": "比较长的译文字幕"}]}

    def split(sentence):
        if sentence == LONG_SRC:
            return "this is a long source line\nthat has to be split"
        return "another long source line\nthat is split in two"

    module = _split_sub(monkeypatch, split=split, align=align, max_length=30)
    translation, split_sub, remerged = (str(tmp_path / name) for name in ("t.xlsx", "s.xlsx", "r.xlsx"))
    pd.DataFrame({
        "Source": [LONG_SRC, "another long source line that is split in two"],
        "Translation": [LONG_TR, "第二行需要切分的比较长的译文字幕"],
    }).to_excel(translation, index=False)
    monkeypatch.setattr(module, "_4_2_TRANSLATION", translation)
    monkeypatch.setattr(module, "_5_SPLIT_SUB", split_sub)
    monkeypatch.setattr(module, "_5_REMERGED", remerged)

    module.split_for_sub_main()

    result = pd.read_excel(split_sub)
    assert result["Source"].tolist() == [LONG_SRC, "another long source line", "that is split in two"]
    assert result["Translation"].tolist() == [LONG_TR, "第二行需要切分的", "比较长的译文字幕"]
    assert not result.isna().any().any()
    assert not pd.read_excel(remerged).isna().any().any()


# ------------------------------------------------------------------
# C7: YouTube cookies (#525)
# ------------------------------------------------------------------

def _ytdlp_options(monkeypatch, tmp_path, youtube):
    import core._1_ytdlp as module

    recorded = {}

    class Download:
        def __init__(self, opts): recorded.update(opts)
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def download(self, urls): pass

    monkeypatch.setattr(module, "load_key", lambda key: youtube)
    monkeypatch.setattr(module, "update_ytdlp", lambda: Download)
    monkeypatch.setattr(module, "find_video_files", lambda path: "synthetic.mp4")
    monkeypatch.setattr(module, "write_input_manifest", lambda *args: None)
    module.download_video_ytdlp("https://video.example.com/item", str(tmp_path))
    return recorded


def test_cookies_file_is_passed_to_the_downloader(monkeypatch, tmp_path):
    cookies = tmp_path / "cookies.txt"
    cookies.write_text("# Netscape HTTP Cookie File\n", encoding="utf-8")

    opts = _ytdlp_options(monkeypatch, tmp_path, {"cookies_path": f' "{cookies}" '})

    assert opts["cookiefile"] == str(cookies)


@pytest.mark.parametrize("youtube", [{}, {"cookies_path": None}, {"cookies_path": ""}, {"cookies_path": "  "}])
def test_download_without_cookies(monkeypatch, tmp_path, youtube):
    assert "cookiefile" not in _ytdlp_options(monkeypatch, tmp_path, youtube)


def test_missing_cookies_file_is_reported(monkeypatch, tmp_path):
    with pytest.raises(ValueError, match="Cookies file not found"):
        _ytdlp_options(monkeypatch, tmp_path, {"cookies_path": str(tmp_path / "nothing.txt")})


@pytest.mark.parametrize("message,expected", [
    ("ERROR: [youtube] abc: Sign in to confirm you’re not a bot. Use --cookies-from-browser or --cookies", True),
    ("ERROR: [youtube] abc: Sign in to confirm your age.", True),
    ("ERROR: unable to download video data: HTTP Error 403: Forbidden", False),
])
def test_needs_cookies(message, expected):
    from core._1_ytdlp import needs_cookies

    assert needs_cookies(Exception(message)) is expected


# ------------------------------------------------------------------
# C8: CosyVoice2 reference audio stays within the limits of the API (#468)
# ------------------------------------------------------------------

def _reference(tmp_path, seconds, frame_rate=44100, channels=2):
    from pydub.generators import Sine

    path = tmp_path / "reference.wav"
    tone = Sine(220, sample_rate=frame_rate).to_audio_segment(duration=seconds * 1000).set_channels(channels)
    tone.export(path, format="wav")
    return path


def _decode_reference(encoded):
    import base64
    import io
    from pydub import AudioSegment

    return AudioSegment.from_file(io.BytesIO(base64.b64decode(encoded)), format="wav")


def test_long_reference_is_cut_with_its_text(tmp_path):
    from core.tts_backend.sf_cosyvoice2 import prepare_reference

    path = _reference(tmp_path, 30)
    text = "one two three four five six seven eight nine ten eleven twelve"

    encoded, prompt_text = prepare_reference(path, text)

    audio = _decode_reference(encoded)
    assert (audio.channels, audio.frame_rate, audio.sample_width) == (1, 24000, 2)
    assert len(audio) == 15000
    assert len(encoded) < os.path.getsize(path) / 4
    assert prompt_text == "one two three four five six"


def test_short_reference_keeps_its_length_and_text(tmp_path):
    from core.tts_backend.sf_cosyvoice2 import prepare_reference

    encoded, prompt_text = prepare_reference(_reference(tmp_path, 4), "这是一句完整的参考文本")

    assert abs(len(_decode_reference(encoded)) - 4000) <= 1
    assert prompt_text == "这是一句完整的参考文本"


def test_long_reference_in_an_unspaced_language(tmp_path):
    from core.tts_backend.sf_cosyvoice2 import prepare_reference

    _, prompt_text = prepare_reference(_reference(tmp_path, 30, 16000, 1), "一二三四五六七八九十")

    assert prompt_text == "一二三四五"


# ------------------------------------------------------------------
# C10: the dub is merged into the video when subtitles are not burned in (#482)
# ------------------------------------------------------------------

def _dub_video(monkeypatch, tmp_path, codec, container, has_background=True):
    import json
    import shutil
    import subprocess
    from pathlib import Path
    from pydub.generators import Sine
    from core import _1_ytdlp, _12_dub_to_vid as merge

    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        pytest.skip('FFmpeg and FFprobe are required')
    monkeypatch.chdir(tmp_path)
    Path('output').mkdir()
    source = Path(f'output/source.{container}')
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'lavfi',
                    '-i', 'color=c=black:s=320x240:r=25:d=6', '-c:v', codec, str(source)], check=True)
    tone = Sine(440, sample_rate=48000).to_audio_segment(duration=6000).apply_gain(-18)
    tone.export('output/dub.mp3', format='mp3', bitrate='64k')
    if has_background:
        tone.apply_gain(-12).export('output/background.wav', format='wav')
    monkeypatch.setattr(_1_ytdlp, 'is_audio_only_input', lambda: False)
    monkeypatch.setattr(merge, 'find_video_files', lambda: str(source))
    monkeypatch.setattr(merge, '_BACKGROUND_AUDIO_FILE', 'output/background.wav')
    monkeypatch.setattr(merge, 'load_key', {'burn_subtitles': False, 'ffmpeg_gpu': False}.__getitem__)
    monkeypatch.setattr(merge, 'check_cancel', lambda: None)
    merge.merge_video_audio()
    probe = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-of', 'json',
                            'output/output_dub.mp4'], check=True, capture_output=True, text=True)
    streams = json.loads(probe.stdout)['streams']
    return {stream['codec_type']: stream for stream in streams}


@pytest.mark.parametrize('has_background', [True, False])
def test_dub_is_merged_without_burning_subtitles(monkeypatch, tmp_path, has_background):
    streams = _dub_video(monkeypatch, tmp_path, 'mpeg4', 'mp4', has_background)

    assert streams['video']['codec_name'] == 'mpeg4'  # copied, not encoded again
    assert streams['audio']['codec_name'] == 'aac'
    assert abs(float(streams['video']['duration']) - 6.0) < 0.1
    assert abs(float(streams['audio']['duration']) - 6.0) < 0.1


def test_video_that_cannot_be_copied_is_encoded_again(monkeypatch, tmp_path):
    streams = _dub_video(monkeypatch, tmp_path, 'flv1', 'flv')

    assert streams['video']['codec_name'] != 'flv1'
    assert abs(float(streams['video']['duration']) - 6.0) < 0.1
    assert streams['audio']['codec_name'] == 'aac'


# ------------------------------------------------------------------
# D1: checkpoint before the translation and transcription only (#175, #255, #483)
# ------------------------------------------------------------------

def _wait_for(condition, timeout=3):
    import time
    end = time.time() + timeout
    while time.time() < end:
        if condition():
            return True
        time.sleep(0.01)
    return False


def _checkpoint(monkeypatch, tmp_path, enabled=True, terminology='{"theme": "t", "terms": []}'):
    from core import pipeline
    from core.task_runner import TaskRunner
    monkeypatch.chdir(tmp_path)
    os.makedirs("output/log")
    with open("output/log/terminology.json", "w", encoding="utf-8") as f:
        f.write(terminology)
    monkeypatch.setattr(pipeline, "load_key", lambda key: {"pause_before_translate": enabled}[key])
    calls = []
    runner = TaskRunner()
    runner.start([("Summarization and multi-step translation", pipeline.review_terminology),
                  ("after", lambda: calls.append("translated"))])
    return pipeline, runner, calls


def _finish_runner(runner):
    runner._thread.join(3)
    assert not runner._thread.is_alive()


def test_task_waits_at_the_checkpoint_until_it_is_resumed(monkeypatch, tmp_path):
    pipeline, runner, calls = _checkpoint(monkeypatch, tmp_path)
    try:
        assert _wait_for(lambda: runner.state == "paused")
        assert runner.pause_message == pipeline.REVIEW_TERMINOLOGY
        assert calls == []
        runner.resume()
        assert runner.pause_message == ""
    finally:
        runner.resume()
        _finish_runner(runner)
    assert runner.state == "completed" and calls == ["translated"]


def test_checkpoint_waits_again_when_the_edit_cannot_be_read(monkeypatch, tmp_path):
    pipeline, runner, calls = _checkpoint(monkeypatch, tmp_path)
    try:
        assert _wait_for(lambda: runner.state == "paused")
        with open("output/log/terminology.json", "w", encoding="utf-8") as f:
            f.write('{"terms": [{"src": "a", "tgt": "b", "note": "c"},]}')
        runner.resume()
        assert _wait_for(lambda: runner.pause_message == pipeline.INVALID_TERMINOLOGY)
        assert runner.state == "paused" and calls == []
        with open("output/log/terminology.json", "w", encoding="utf-8") as f:
            f.write('{"terms": [{"src": "a", "tgt": "b", "note": "c"}]}')
        runner.resume()
    finally:
        runner.resume()
        _finish_runner(runner)
    assert runner.state == "completed" and calls == ["translated"]


def test_checkpoint_can_be_stopped(monkeypatch, tmp_path):
    _, runner, calls = _checkpoint(monkeypatch, tmp_path)
    try:
        assert _wait_for(lambda: runner.state == "paused")
    finally:
        runner.stop()
        _finish_runner(runner)
    assert runner.state == "stopped" and runner.pause_message == "" and calls == []


def test_no_checkpoint_when_it_is_switched_off(monkeypatch, tmp_path):
    _, runner, calls = _checkpoint(monkeypatch, tmp_path, enabled=False)
    _finish_runner(runner)
    assert runner.state == "completed" and calls == ["translated"]


def test_no_checkpoint_when_the_translation_exists(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    os.makedirs("output/log")
    open("output/log/translation_results.xlsx", "w").close()
    from core.utils.models import _4_2_TRANSLATION
    assert _4_2_TRANSLATION == "output/log/translation_results.xlsx"
    from core import pipeline
    from core.task_runner import TaskRunner
    monkeypatch.setattr(pipeline, "load_key", lambda key: True)
    runner = TaskRunner()
    runner.start([("one", pipeline.review_terminology)])
    _finish_runner(runner)
    assert runner.state == "completed"


def test_checkpoint_does_nothing_outside_a_task(monkeypatch, tmp_path):
    from core import pipeline
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(pipeline, "load_key", lambda key: True)
    pipeline.review_terminology()


@pytest.mark.parametrize("content,valid", [
    ('{"theme": "t", "terms": [{"src": "a", "tgt": "b", "note": "c"}]}', True),
    ('{"terms": []}', True),
    ('{"terms": [{"src": "a", "tgt": "b"}]}', False),
    ('{"terms": {"src": "a"}}', False),
    ('[]', False),
    ('not json', False),
])
def test_terminology_error(monkeypatch, tmp_path, content, valid):
    from core import pipeline
    monkeypatch.chdir(tmp_path)
    os.makedirs("output/log")
    with open("output/log/terminology.json", "w", encoding="utf-8") as f:
        f.write(content)
    assert (pipeline.terminology_error() is None) == valid


def test_edited_terminology_is_kept_on_a_retry(monkeypatch, tmp_path):
    import core._4_1_summarize as module
    monkeypatch.chdir(tmp_path)
    os.makedirs("output/log")
    with open("output/log/terminology.json", "w", encoding="utf-8") as f:
        f.write('{"terms": [{"src": "edited", "tgt": "b", "note": "c"}]}')
    monkeypatch.setattr(module, "ask_gpt", lambda *args, **kwargs: pytest.fail("summarized again"))

    module.get_summary()

    with open("output/log/terminology.json", encoding="utf-8") as f:
        assert "edited" in f.read()


def test_transcribe_stage_stops_before_the_translation(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from core import pipeline
    monkeypatch.chdir(tmp_path)
    calls = []
    monkeypatch.setattr(pipeline, "import_module", lambda name: SimpleNamespace(**{
        function: lambda call=f"{name}.{function}": calls.append(call)
        for function in ("import_subtitles", "transcribe", "split_by_spacy", "split_sentences_by_meaning",
                         "gen_source_subtitles")}))

    steps = pipeline.get_steps("transcribe")
    for _, step in steps:
        step()

    assert [label for label, _ in steps] == [
        "Word-level transcription and alignment", "Sentence segmentation using NLP and LLM", "Generate subtitle files"]
    assert calls == ["core._2_import_subtitles.import_subtitles", "core._2_asr.transcribe",
                     "core._3_1_split_nlp.split_by_spacy",
                     "core._3_2_split_meaning.split_sentences_by_meaning", "core._6_gen_sub.gen_source_subtitles"]
    assert not os.path.exists("output/.subtitle_done")


def test_source_subtitles_without_a_translation(monkeypatch, tmp_path):
    import core._5_split_sub as split_sub
    import core._6_gen_sub as module
    monkeypatch.chdir(tmp_path)
    os.makedirs("output/log")
    _words().to_excel("output/log/cleaned_chunks.xlsx", index=False)
    with open("output/log/split_by_meaning.txt", "w", encoding="utf-8") as f:
        f.write("Hello world.\nHow are you?\n")
    settings = {"subtitle": {"max_length": 8, "target_multiplier": 1.2}, "max_workers": 2}
    monkeypatch.setattr(split_sub, "load_key", lambda key: settings[key])
    split = {"Hello world.": "Hello\nworld.", "How are you?": "How are\nyou?"}
    monkeypatch.setattr(split_sub, "split_sentence", lambda sentence, num_parts: split.get(sentence, sentence))

    module.gen_source_subtitles()

    assert [name for name in os.listdir("output") if name != "log"] == ["src.srt"]
    with open("output/src.srt", encoding="utf-8") as f:
        assert f.read() == (
            "1\n00:00:00,000 --> 00:00:00,500\nHello\n\n\n"
            "2\n00:00:00,500 --> 00:00:01,000\nworld.\n\n\n"
            "3\n00:00:02,000 --> 00:00:02,800\nHow are\n\n\n"
            "4\n00:00:02,800 --> 00:00:03,200\nyou?"
        )


# ------------------------------------------------------------------
# D2: the style of the burned-in subtitles is configurable (#460)
# ------------------------------------------------------------------

def _style(monkeypatch, configured):
    import core.utils.subtitle_style as module
    monkeypatch.setattr(module, "load_key_or", lambda key, default: configured if key == "subtitle.style" else default)
    monkeypatch.setattr(module, "default_font", lambda: "Arial")
    return module


@pytest.mark.parametrize("configured", [None, {}, {"source": None}, "bold"])
def test_default_subtitle_style(monkeypatch, configured):
    module = _style(monkeypatch, configured)

    assert module.get_force_style("source") == (
        "FontSize=15,FontName=Arial,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=1,BorderStyle=1")
    assert module.get_force_style("translation") == (
        "FontSize=17,FontName=Arial,PrimaryColour=&H00FFFF,OutlineColour=&H000000,Outline=1,"
        "BackColour=&H33000000,Alignment=2,MarginV=27,BorderStyle=4")


def test_configured_subtitle_style(monkeypatch):
    module = _style(monkeypatch, {"translation": {
        "font_name": "Noto Sans CJK SC", "font_size": 22, "font_color": "#ff8000",
        "outline_width": 2.5, "back_color": "&h80000000", "margin_v": 40}})

    assert module.get_force_style("translation") == (
        "FontSize=22,FontName=Noto Sans CJK SC,PrimaryColour=&H0080FF,OutlineColour=&H000000,Outline=2.5,"
        "BackColour=&H80000000,Alignment=2,MarginV=40,BorderStyle=4")
    assert module.get_force_style("source").startswith("FontSize=15,FontName=Arial,")


@pytest.mark.parametrize("key,value", [
    ("font_name", "Arial',drawtext=text=x"), ("font_name", "a:b"), ("font_name", 3),
    ("font_size", "big"), ("font_size", -1), ("font_size", True),
    ("font_color", "red"), ("font_color", "&HFFF"), ("font_color", "#ff80001"),
    ("margin_v", None),
])
def test_unusable_style_value_falls_back_to_the_default(monkeypatch, key, value):
    module = _style(monkeypatch, {"translation": {key: value}})

    assert module.get_subtitle_style("translation") == module.DEFAULT_STYLE["translation"]


@pytest.mark.parametrize("value,ass,hex_color", [
    ("&H00FFFF", "&H00FFFF", "#ffff00"),
    ("&h3300ff80", "&H3300FF80", "#80ff00"),
    ("#FF8000", "&H0080FF", "#ff8000"),
])
def test_subtitle_colors(value, ass, hex_color):
    from core.utils.subtitle_style import to_ass_color, to_hex_color
    assert to_ass_color(value) == ass
    assert to_hex_color(ass) == hex_color


def test_style_is_read_from_a_config_without_the_key(monkeypatch, tmp_path):
    import core.utils.config_utils as config_utils
    import core.utils.subtitle_style as module
    (tmp_path / "config.yaml").write_text("subtitle:\n  max_length: 75\n", encoding="utf-8")
    monkeypatch.setattr(config_utils, "CONFIG_PATH", str(tmp_path / "config.yaml"))

    assert module.get_subtitle_style("source") == module.DEFAULT_STYLE["source"]
    assert config_utils.update_key("subtitle.style", {"source": {"font_size": 20}}, add_missing=True)
    assert module.get_subtitle_style("source")["font_size"] == 20
    assert module.get_subtitle_style("translation") == module.DEFAULT_STYLE["translation"]


def test_saving_the_style_keeps_the_comments(monkeypatch, tmp_path):
    import core.utils.config_utils as config_utils
    import core.utils.subtitle_style as module
    config = tmp_path / "config.yaml"
    config.write_text(
        "subtitle:\n  style:\n    source:\n      font_size: 15\n    translation:\n      # below the video\n"
        "      margin_v: 27\n\n# *Summary length\nsummary_length: 8000\n", encoding="utf-8")
    monkeypatch.setattr(config_utils, "CONFIG_PATH", str(config))

    style = {kind: module.get_subtitle_style(kind) for kind in ("source", "translation")}
    style["source"]["font_size"] = 20
    style["translation"]["font_name"] = "Helvetica"
    module.save_subtitle_style(style)

    text = config.read_text(encoding="utf-8")
    assert "# *Summary length" in text and "# below the video" in text
    assert module.get_subtitle_style("source")["font_size"] == 20
    assert module.get_subtitle_style("translation") == {**module.DEFAULT_STYLE["translation"], "font_name": "Helvetica"}
    assert "outline_width" not in text  # only the changed values are written


@pytest.mark.parametrize("content", ["subtitle:\n  max_length: 75\n", "subtitle:\n  style:\n    source: big\n"])
def test_saving_the_style_without_a_usable_one(monkeypatch, tmp_path, content):
    import core.utils.config_utils as config_utils
    import core.utils.subtitle_style as module
    (tmp_path / "config.yaml").write_text(content, encoding="utf-8")
    monkeypatch.setattr(config_utils, "CONFIG_PATH", str(tmp_path / "config.yaml"))

    style = {kind: module.get_subtitle_style(kind) for kind in ("source", "translation")}
    style["source"]["font_size"] = 20
    module.save_subtitle_style(style)

    assert module.get_subtitle_style("source") == {**module.DEFAULT_STYLE["source"], "font_size": 20}
    assert module.get_subtitle_style("translation") == module.DEFAULT_STYLE["translation"]


# ------------------------------------------------------------------
# D4: the style of the translation in the words of the user (#112, #504)
# ------------------------------------------------------------------

STYLE_SECTION = (
    "### Translation Style\n"
    "The user asks for the following style. Follow it in the translation, without changing the meaning of the original:\n"
    "<translation_style>\ncolloquial, short sentences\n</translation_style>\n\n"
)


def _prompts(monkeypatch, style, reflect, **missing):
    import core.prompts as prompts
    settings = {"target_language": "简体中文", "reflect_translate": reflect}
    monkeypatch.setattr(prompts, "load_key", lambda key: settings[key])
    monkeypatch.setattr(prompts, "load_key_or", lambda key, default: default if missing else style)
    monkeypatch.setattr(prompts, "get_source_language", lambda: "en")
    shared = prompts.generate_shared_prompt("before", "after", "summary", "notes")
    faithful = {"1": {"origin": "Hello.", "direct": "你好。"}}
    return prompts.get_prompt_faithfulness("Hello.", shared), prompts.get_prompt_expressiveness(faithful, "Hello.", shared)


@pytest.mark.parametrize("reflect", [True, False])
@pytest.mark.parametrize("style", ["", "   ", None])
def test_prompts_without_a_translation_style(monkeypatch, reflect, style):
    plain = _prompts(monkeypatch, "", reflect, missing=True)

    assert _prompts(monkeypatch, style, reflect) == plain
    assert not any("Translation Style" in prompt for prompt in plain)
    assert "</subsequent_content>" in plain[0] and "notes\n\n<translation_principles>" in plain[0]
    assert "notes\n\n<Translation Analysis Steps>" in plain[1]


def test_translation_style_goes_into_the_polish_step(monkeypatch):
    plain = _prompts(monkeypatch, "", True)
    faithfulness, expressiveness = _prompts(monkeypatch, " colloquial, short sentences\n", True)

    assert faithfulness == plain[0]
    assert expressiveness == plain[1].replace("<Translation Analysis Steps>", STYLE_SECTION + "<Translation Analysis Steps>")


def test_translation_style_without_the_polish_step(monkeypatch):
    plain = _prompts(monkeypatch, "", False)
    faithfulness, _ = _prompts(monkeypatch, "colloquial, short sentences", False)

    assert faithfulness == plain[0].replace("<translation_principles>", STYLE_SECTION + "<translation_principles>")


# ------------------------------------------------------------------
# D3: which subtitles are burned into the two videos (#338, #348, #464)
# ------------------------------------------------------------------

def _burn(monkeypatch, tmp_path, configured, files=("src.srt", "trans.srt")):
    import core.utils.subtitle_style as module
    monkeypatch.chdir(tmp_path)
    for name in files:
        open(name, "w").close()
    monkeypatch.setattr(module, "load_key_or", lambda key, default: configured.get(key, default))
    monkeypatch.setattr(module, "get_force_style", lambda kind: kind.upper())
    return module


@pytest.mark.parametrize("video,configured,expected", [
    ("subtitle", {}, "subtitles=src.srt:force_style='SOURCE',subtitles=trans.srt:force_style='TRANSLATION'"),
    ("dubbed", {}, "subtitles=trans.srt:force_style='TRANSLATION'"),
    ("subtitle", {"subtitle.sub_video_subtitles": "translation"}, "subtitles=trans.srt:force_style='TRANSLATION'"),
    ("subtitle", {"subtitle.sub_video_subtitles": "source"}, "subtitles=src.srt:force_style='SOURCE'"),
    ("dubbed", {"subtitle.dub_video_subtitles": "bilingual"},
     "subtitles=src.srt:force_style='SOURCE',subtitles=trans.srt:force_style='TRANSLATION'"),
    ("dubbed", {"subtitle.sub_video_subtitles": "source"}, "subtitles=trans.srt:force_style='TRANSLATION'"),
    ("subtitle", {"subtitle.sub_video_subtitles": "both"},
     "subtitles=src.srt:force_style='SOURCE',subtitles=trans.srt:force_style='TRANSLATION'"),
    ("dubbed", {"subtitle.dub_video_subtitles": None}, "subtitles=trans.srt:force_style='TRANSLATION'"),
])
def test_subtitle_filters(monkeypatch, tmp_path, video, configured, expected):
    module = _burn(monkeypatch, tmp_path, configured)

    assert module.get_subtitle_filters(video, "src.srt", "trans.srt") == expected


@pytest.mark.parametrize("mode", ["bilingual", "source"])
def test_dub_without_source_subtitles_burns_the_translation(monkeypatch, tmp_path, mode):
    module = _burn(monkeypatch, tmp_path, {"subtitle.dub_video_subtitles": mode}, files=("trans.srt",))

    assert module.get_subtitle_filters("dubbed", "src.srt", "trans.srt") == "subtitles=trans.srt:force_style='TRANSLATION'"


def test_default_subtitle_filter_is_the_one_from_before(monkeypatch, tmp_path):
    module = _style(monkeypatch, None)
    monkeypatch.chdir(tmp_path)
    os.makedirs("output")
    for name in ("src.srt", "trans.srt", "dub.srt"):
        open(f"output/{name}", "w").close()

    assert module.get_subtitle_filters("subtitle", "output/src.srt", "output/trans.srt") == (
        f"subtitles=output/src.srt:force_style='{module.get_force_style('source')}',"
        f"subtitles=output/trans.srt:force_style='{module.get_force_style('translation')}'")
    assert module.get_subtitle_filters("dubbed", "output/dub_src.srt", "output/dub.srt") == (
        f"subtitles=output/dub.srt:force_style='{module.get_force_style('translation')}'")


def _dub_subtitle_tasks(tmp_path, monkeypatch, **columns):
    import core._11_merge_audio as module
    monkeypatch.chdir(tmp_path)
    os.makedirs("output/audio")
    pd.DataFrame({
        "number": [1, 2],
        "lines": [str(["你好。", "最近好吗？"]), str(["再见。"])],
        "new_sub_times": [str([[0.0, 1.5], [1.5, 3.25]]), str([[3661.5, 3663.0]])],
        **columns,
    }).to_excel("output/audio/tts_tasks.xlsx", index=False)
    return module


def test_dub_subtitles_in_both_languages(monkeypatch, tmp_path):
    module = _dub_subtitle_tasks(tmp_path, monkeypatch, src_lines=[str(["Hello.", "How are you?"]), str(["Bye."])])

    module.create_srt_subtitle()

    with open("output/dub.srt", encoding="utf-8") as f:
        assert f.read() == (
            "1\n00:00:00,000 --> 00:00:01,500\n你好。\n\n"
            "2\n00:00:01,500 --> 00:00:03,250\n最近好吗？\n\n"
            "3\n01:01:01,500 --> 01:01:03,000\n再见。\n\n")
    with open("output/dub_src.srt", encoding="utf-8") as f:
        assert f.read() == (
            "1\n00:00:00,000 --> 00:00:01,500\nHello.\n\n"
            "2\n00:00:01,500 --> 00:00:03,250\nHow are you?\n\n"
            "3\n01:01:01,500 --> 01:01:03,000\nBye.\n\n")


@pytest.mark.parametrize("columns", [
    {},
    {"src_lines": [str(["Hello."]), str(["Bye."])]},
    {"src_lines": [None, None]},
])
def test_no_source_subtitles_of_the_dub_when_they_do_not_match(monkeypatch, tmp_path, columns):
    module = _dub_subtitle_tasks(tmp_path, monkeypatch, **columns)
    open("output/dub_src.srt", "w").close()

    module.create_srt_subtitle()

    assert sorted(os.listdir("output")) == ["audio", "dub.srt"]


# ------------------------------------------------------------------
# D1: checkpoint after the translation (#355, #483, #571)
# ------------------------------------------------------------------

def _translation_results(translation, source=("Hello world.", "...", "How are you?")):
    pd.DataFrame({"Source": list(source), "Translation": list(translation),
                  "timestamp": ["00:00:00,000 --> 00:00:01,000"] * len(source), "duration": [1.0] * len(source),
                  }).to_excel("output/log/translation_results.xlsx", index=False)


def _translation_checkpoint(monkeypatch, tmp_path, enabled=True):
    from core import pipeline
    from core.task_runner import TaskRunner
    monkeypatch.chdir(tmp_path)
    os.makedirs("output/log")
    _translation_results(["你好，世界。", None, "你好吗？"])
    monkeypatch.setattr(pipeline, "load_key_or", lambda key, default: {"pause_after_translate": enabled}[key])
    calls = []
    runner = TaskRunner()
    runner.start([("Summarization and multi-step translation", pipeline.review_translation),
                  ("after", lambda: calls.append("subtitles"))])
    return pipeline, runner, calls


def test_task_waits_after_the_translation_and_uses_the_edit(monkeypatch, tmp_path):
    pipeline, runner, calls = _translation_checkpoint(monkeypatch, tmp_path)
    try:
        assert _wait_for(lambda: runner.state == "paused")
        assert runner.pause_message == pipeline.REVIEW_TRANSLATION
        assert calls == []
        _translation_results(["大家好。", None, "你好吗？"])
        runner.resume()
    finally:
        runner.resume()
        _finish_runner(runner)
    assert runner.state == "completed" and calls == ["subtitles"]
    assert pipeline.read_translation() == [["Hello world.", "...", "How are you?"], ["大家好。", "", "你好吗？"]]


@pytest.mark.parametrize("edit", [
    lambda: _translation_results(["你好，世界。", None], source=["Hello world.", "..."]),
    lambda: _translation_results(["你好，世界。", None, "你好吗？"], source=["Hello, world.", "...", "How are you?"]),
    lambda: _translation_results(["你好，世界。", None, " "]),
    lambda: pd.DataFrame({"Source": ["Hello world.", "...", "How are you?"]}).to_excel(
        "output/log/translation_results.xlsx", index=False),
    lambda: open("output/log/translation_results.xlsx", "w").close(),
    lambda: os.remove("output/log/translation_results.xlsx"),
])
def test_checkpoint_waits_again_when_the_translation_cannot_be_used(monkeypatch, tmp_path, edit):
    pipeline, runner, calls = _translation_checkpoint(monkeypatch, tmp_path)
    try:
        assert _wait_for(lambda: runner.state == "paused")
        edit()
        runner.resume()
        assert _wait_for(lambda: runner.pause_message == pipeline.INVALID_TRANSLATION)
        assert runner.state == "paused" and calls == []
        _translation_results(["你好，世界。", "……", "你好吗？"])
        runner.resume()
    finally:
        runner.resume()
        _finish_runner(runner)
    assert runner.state == "completed" and calls == ["subtitles"]


def test_checkpoint_after_the_translation_can_be_stopped(monkeypatch, tmp_path):
    _, runner, calls = _translation_checkpoint(monkeypatch, tmp_path)
    try:
        assert _wait_for(lambda: runner.state == "paused")
    finally:
        runner.stop()
        _finish_runner(runner)
    assert runner.state == "stopped" and calls == []


def test_no_checkpoint_after_the_translation_when_it_is_switched_off(monkeypatch, tmp_path):
    _, runner, calls = _translation_checkpoint(monkeypatch, tmp_path, enabled=False)
    _finish_runner(runner)
    assert runner.state == "completed" and calls == ["subtitles"]


def test_no_checkpoint_when_the_subtitles_are_cut_already(monkeypatch, tmp_path):
    from core import pipeline
    from core.task_runner import TaskRunner
    from core.utils.models import _5_SPLIT_SUB
    monkeypatch.chdir(tmp_path)
    os.makedirs("output/log")
    open(_5_SPLIT_SUB, "w").close()
    monkeypatch.setattr(pipeline, "load_key_or", lambda key, default: True)
    runner = TaskRunner()
    runner.start([("one", pipeline.review_translation)])
    _finish_runner(runner)
    assert runner.state == "completed"


def test_checkpoint_after_the_translation_is_off_without_the_key(monkeypatch, tmp_path):
    from core import pipeline
    from core.task_runner import TaskRunner
    monkeypatch.chdir(tmp_path)
    with open("config.yaml", "w", encoding="utf-8") as f:
        f.write("pause_before_translate: true\n")
    runner = TaskRunner()
    runner.start([("one", pipeline.review_translation)])
    _finish_runner(runner)
    assert runner.state == "completed"
    pipeline.review_translation()


def test_translation_is_reviewed_before_the_subtitles_are_cut():
    from core import pipeline
    calls = [call for _, calls in pipeline.SUBTITLE_STEPS for call in calls]
    assert calls[calls.index("_4_2_translate.translate_all") + 1:][:2] == [
        "pipeline.review_translation", "_5_split_sub.split_for_sub_main"]


# ------------------------------------------------------------------
# D1: subtitles of the user instead of the recognition (#255, #457, #476)
# ------------------------------------------------------------------

SRT = """1
00:00:01,000 --> 00:00:03,000
<i>Hello</i> world.

2
00:00:03,500 --> 00:00:05,000
{\\an8}- How are you?
- Fine, <font color="#ffff00">thanks</font>.

3
00:00:05,000 --> 00:00:06,000
♪♪

4
00:01:00.250 --> 01:00:02.5
2024

5
00:00:07,000 --> 00:00:08,000
Pneumonoultramicroscopicsilicovolcanoconiosis 你好，世界
"""
CUES = [
    (1.0, 3.0, "Hello world."),
    (3.5, 5.0, "- How are you? - Fine, thanks."),
    (7.0, 8.0, "Pneumonoultramicroscopicsilicovolcanoconiosis 你好，世界"),
    (60.25, 3602.5, "2024"),
]


@pytest.mark.parametrize("content", [
    SRT.encode("utf-8"),
    SRT.replace("\n", "\r\n").encode("utf-8-sig"),
    SRT.encode("utf-16"),
    SRT.replace("\n\n", "\n").encode("utf-8"),
])
def test_subtitles_of_an_srt_file(content):
    from core._2_import_subtitles import read_cues
    assert read_cues(content) == CUES


@pytest.mark.parametrize("content", [
    b"", b"Hello world.", "1\n00:00:01,000 --> 00:00:02,000\n♪\n".encode("utf-8"),
    "1\n00:00:01,000 --> 00:00:02,000\n你好\n".encode("gbk"),
    "1\n00:00:02,000 --> 00:00:02,000\nHello\n".encode("utf-8"),
])
def test_file_without_subtitles_is_refused(content):
    from core._2_import_subtitles import read_cues
    with pytest.raises(ValueError):
        read_cues(content)


def _input_subtitles(monkeypatch, tmp_path, video=False, language="en"):
    import core._2_import_subtitles as module
    from core._1_ytdlp import write_input_manifest
    monkeypatch.chdir(tmp_path)
    with open("config.yaml", "w", encoding="utf-8") as f:
        f.write(f"allowed_video_formats: [mp4]\nallowed_audio_formats: [mp3]\ndemucs: false\n"
                f"whisper:\n  language: {language}\n")
    os.makedirs("output")
    if video:
        open("output/talk.mp4", "w").close()
        write_input_manifest("output/talk.mp4", "video")
    return module


def test_subtitles_are_the_input_without_a_media_file(monkeypatch, tmp_path):
    from core import _1_ytdlp
    module = _input_subtitles(monkeypatch, tmp_path)

    subtitle_file = module.add_input_subtitles("my: talk.srt", SRT.encode("utf-8"))

    assert subtitle_file == os.path.join("output", "input", "my talk.srt")
    assert _1_ytdlp.find_media_file() == (subtitle_file, "subtitle")
    assert _1_ytdlp.find_subtitle_file() == subtitle_file
    assert _1_ytdlp.is_audio_only_input()


def test_subtitles_go_with_the_video(monkeypatch, tmp_path):
    from core import _1_ytdlp
    module = _input_subtitles(monkeypatch, tmp_path, video=True)
    assert _1_ytdlp.find_subtitle_file() is None

    subtitle_file = module.add_input_subtitles("talk.srt", SRT.encode("utf-8"))

    assert _1_ytdlp.find_media_file() == ("output/talk.mp4", "video")
    assert _1_ytdlp.find_subtitle_file() == subtitle_file
    assert not _1_ytdlp.is_audio_only_input()


def test_file_without_subtitles_is_not_added(monkeypatch, tmp_path):
    module = _input_subtitles(monkeypatch, tmp_path)
    with pytest.raises(ValueError):
        module.add_input_subtitles("talk.srt", b"Hello world.")
    assert os.listdir("output") == []


def test_subtitles_take_the_place_of_the_recognition(monkeypatch, tmp_path):
    from core._6_gen_sub import get_sentence_timestamps
    module = _input_subtitles(monkeypatch, tmp_path)
    module.add_input_subtitles("talk.srt", SRT.encode("utf-8"))

    module.import_subtitles()

    sentences = [text for _, _, text in CUES]
    for name in ("split_by_nlp.txt", "split_by_meaning.txt"):
        with open(f"output/log/{name}", encoding="utf-8") as f:
            assert f.read().split("\n") == sentences
    words = pd.read_excel("output/log/cleaned_chunks.xlsx")
    assert list(words.columns) == ["text", "start", "end", "speaker_id"]
    assert list(words["text"][:2]) == ['"Hello"', '"world."'] and len(words) == 12
    assert list(words["start"][:3]) == [1.0, 2.0, 3.5] and list(words["end"][:3]) == [2.0, 3.0, 3.5]
    # The lines get the times of their subtitles back
    words["text"] = words["text"].str.strip('"')
    stamps = get_sentence_timestamps(words, pd.DataFrame({"Source": sentences}))
    assert stamps == [(start, end) for start, end, _ in CUES]


def test_subtitles_with_a_video_prepare_the_audio_of_the_dubbing(monkeypatch, tmp_path):
    import core._2_asr as asr
    module = _input_subtitles(monkeypatch, tmp_path, video=True)
    module.add_input_subtitles("talk.srt", SRT.encode("utf-8"))
    calls = []
    monkeypatch.setattr(asr, "prepare_audio", lambda *args: calls.append(args))

    module.import_subtitles()

    assert calls == [("output/talk.mp4", "video", False)]
    assert os.path.exists("output/log/cleaned_chunks.xlsx")


def test_subtitles_without_a_video_need_no_audio(monkeypatch, tmp_path):
    import core._2_asr as asr
    module = _input_subtitles(monkeypatch, tmp_path)
    module.add_input_subtitles("talk.srt", SRT.encode("utf-8"))
    monkeypatch.setattr(asr, "prepare_audio", lambda *args: pytest.fail("there is no audio"))

    module.import_subtitles()

    assert os.path.exists("output/log/cleaned_chunks.xlsx")


def test_subtitles_need_their_language(monkeypatch, tmp_path):
    module = _input_subtitles(monkeypatch, tmp_path, language="auto")
    module.add_input_subtitles("talk.srt", SRT.encode("utf-8"))
    with pytest.raises(ValueError, match="language"):
        module.import_subtitles()
    assert not os.path.exists("output/log")


def test_recognition_is_kept_without_subtitles_of_the_user(monkeypatch, tmp_path):
    module = _input_subtitles(monkeypatch, tmp_path, video=True)
    module.import_subtitles()
    assert not os.path.exists("output/log")

    # A retry keeps the words that are there
    module.add_input_subtitles("talk.srt", SRT.encode("utf-8"))
    os.makedirs("output/log")
    _words().to_excel("output/log/cleaned_chunks.xlsx", index=False)
    module.import_subtitles()
    assert len(pd.read_excel("output/log/cleaned_chunks.xlsx")) == 5
    assert os.listdir("output/log") == ["cleaned_chunks.xlsx"]


def test_subtitles_of_the_user_are_not_cut(monkeypatch, tmp_path):
    import core._5_split_sub as module
    monkeypatch.chdir(tmp_path)
    os.makedirs("output/log")
    _translation_results(["大家好。" * 30, "……", "你好吗？"])
    monkeypatch.setattr(module, "find_subtitle_file", lambda: "output/input/talk.srt")
    monkeypatch.setattr(module, "split_align_subs", lambda *args: pytest.fail("the lines are kept"))

    module.split_for_sub_main()

    for name in ("translation_results_for_subtitles.xlsx", "translation_results_remerged.xlsx"):
        df = pd.read_excel(f"output/log/{name}")
        assert list(df["Source"]) == ["Hello world.", "...", "How are you?"]
        assert list(df["Translation"]) == ["大家好。" * 30, "……", "你好吗？"]


def test_source_subtitles_of_the_user_are_not_cut(monkeypatch, tmp_path):
    import core._1_ytdlp as ytdlp
    import core._5_split_sub as split_sub
    import core._6_gen_sub as module
    monkeypatch.chdir(tmp_path)
    os.makedirs("output/log")
    _words().to_excel("output/log/cleaned_chunks.xlsx", index=False)
    with open("output/log/split_by_meaning.txt", "w", encoding="utf-8") as f:
        f.write("Hello world.\nHow are you?")
    monkeypatch.setattr(ytdlp, "find_subtitle_file", lambda: "output/input/talk.srt")
    monkeypatch.setattr(split_sub, "split_source_lines", lambda lines: pytest.fail("the lines are kept"))

    module.gen_source_subtitles()

    with open("output/src.srt", encoding="utf-8") as f:
        assert f.read() == ("1\n00:00:00,000 --> 00:00:01,000\nHello world.\n\n\n"
                            "2\n00:00:02,000 --> 00:00:03,200\nHow are you?")


def test_subtitles_are_imported_before_the_recognition():
    from core import pipeline
    assert pipeline.SUBTITLE_STEPS[0][1] == ("_2_import_subtitles.import_subtitles", "_2_asr.transcribe")
    assert pipeline.TRANSCRIBE_STEPS[0] == pipeline.SUBTITLE_STEPS[0]


# ------------------------------------------------------------------
# Dubbing: a failed request is an error, not a silent line
# ------------------------------------------------------------------

class _Refused:
    status_code = 401
    text = '{"error": "invalid key"}'
    content = b'{"error": "invalid key"}'

    def json(self):
        return {"error": "invalid key"}


def test_refused_azure_request_is_not_saved_as_audio(monkeypatch, tmp_path):
    from core.tts_backend import azure_tts

    monkeypatch.setattr(azure_tts, "load_key", lambda key: "value")
    monkeypatch.setattr(azure_tts.requests, "request", lambda *args, **kwargs: _Refused())
    audio = tmp_path / "1.wav"

    with pytest.raises(ValueError, match="401"):
        azure_tts.azure_tts("Hello", str(audio))

    assert not audio.exists()


def test_refused_openai_request_is_an_error(monkeypatch, tmp_path):
    from core.tts_backend import openai_tts

    monkeypatch.setattr(openai_tts, "load_key", lambda key: "alloy" if key.endswith("voice") else "value")
    monkeypatch.setattr(openai_tts.requests, "post", lambda *args, **kwargs: _Refused())
    monkeypatch.setattr("time.sleep", lambda seconds: None)
    audio = tmp_path / "1.wav"

    with pytest.raises(ValueError, match="401"):
        openai_tts.openai_tts("Hello", str(audio))

    assert not audio.exists()


def test_dubbing_stops_when_the_service_refuses(monkeypatch, tmp_path):
    from core.tts_backend import tts_main

    def refuse(text, save_as):
        raise ValueError("Azure TTS request failed: HTTP 401")

    monkeypatch.setattr(tts_main, "load_key", lambda key: "azure_tts")
    monkeypatch.setattr(tts_main, "azure_tts", refuse)
    monkeypatch.setattr(tts_main, "ask_gpt", lambda *args, **kwargs: {"text": "Hello there"})
    audio = tmp_path / "1.wav"

    with pytest.raises(Exception, match="401"):
        tts_main.tts_main("Hello there", str(audio), 1, None)

    assert not audio.exists()


# ------------------------------------------------------------------
# Dubbing: the duration of Japanese text, hyphens inside words
# ------------------------------------------------------------------

def test_japanese_text_is_not_estimated_as_chinese():
    from core.tts_backend.estimate_duration import init_estimator, estimate_duration

    estimator = init_estimator()
    # 3 kanji and 17 kana: as Chinese, the kana were left out and the estimate was 1.9 s for 4.9 s
    japanese = estimate_duration("皆さん、こんにちは 新しいエピソードの始まりです", estimator)
    chinese = estimate_duration("大家好，欢迎收看新的一期", estimator)

    assert 4 < japanese < 5.5
    assert chinese == pytest.approx(11 * 0.21 + 0.1)
