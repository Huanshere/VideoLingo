"""Batched LLM requests: one request per group, item-by-item checks, no-LLM fallback."""

from unittest.mock import patch

import pytest

from core import llm_batch
from core import _3_2_split_meaning as split_meaning

SETTINGS = {"whisper.language": "en", "target_language": "Hindi"}


@pytest.fixture(autouse=True)
def config(monkeypatch):
    monkeypatch.setattr(split_meaning, "load_key", lambda key: SETTINGS[key])
    monkeypatch.setattr(llm_batch, "load_key", lambda key: SETTINGS[key])
    monkeypatch.setattr(llm_batch, "get_source_language", lambda: "English")
    monkeypatch.setattr(llm_batch, "check_cancel", lambda: None)
    monkeypatch.setattr(llm_batch, "load_key_or", lambda key, default: {"llm_batch_size": 2}.get(key, default))


def test_sentences_are_split_with_one_request_per_group():
    items = [("one two three four five six", 2, 3), ("alpha beta gamma delta epsilon zeta", 2, 3),
             ("red green blue cyan magenta yellow", 2, 3)]
    replies = [
        {"splits": [{"id": 1, "split": "one two three [br] four five six"},
                    {"id": 2, "split": "alpha beta gamma<br>delta epsilon zeta"}]},
        {"splits": [{"id": 1, "split": "red green blue [br] cyan magenta yellow"}]},
    ]
    with patch.object(llm_batch, "ask_gpt", side_effect=replies) as ask:
        out = llm_batch.batch_split(items)
    assert ask.call_count == 2  # 3 items, groups of 2
    assert out == ["one two three\nfour five six", "alpha beta gamma\ndelta epsilon zeta",
                   "red green blue\ncyan magenta yellow"]
    prompt = ask.call_args_list[0].args[0]
    assert '"id": 1' in prompt and "one two three four five six" in prompt


def test_missing_or_altered_items_fall_back_without_another_request():
    items = [("one two three four five six", 2, 3), ("alpha beta gamma delta epsilon zeta", 2, 3)]
    reply = {"splits": [{"id": 1, "split": "a completely different sentence [br] here"}]}
    with patch.object(llm_batch, "ask_gpt", return_value=reply) as ask:
        out = llm_batch.batch_split(items)
    assert ask.call_count == 1
    assert out == [split_meaning.mechanical_split(s, n) for s, n, _ in items]


def test_a_failed_request_uses_the_fallback_for_its_group():
    items = [("one two three four five six", 2, 3)]
    with patch.object(llm_batch, "ask_gpt", side_effect=RuntimeError("Error code: 429")):
        assert llm_batch.batch_split(items) == [split_meaning.mechanical_split(*items[0][:2])]


def test_alignments_need_exactly_one_part_per_source_part():
    items = [("a b", "क ख", ["a", "b"]), ("c d", "ग घ", ["c", "d"]), ("e f", "च छ", ["e", "f"])]
    replies = [{"aligns": [{"id": 1, "target_parts": ["क", "ख"]}, {"id": 2, "target_parts": ["ग घ"]}]},
               {"aligns": [{"id": 1, "target_parts": ["च", " "]}]}]
    with patch.object(llm_batch, "ask_gpt", side_effect=replies) as ask:
        assert llm_batch.batch_align(items) == [["क", "ख"], None, None]
    assert ask.call_count == 2
