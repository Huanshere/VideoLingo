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
