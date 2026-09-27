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
