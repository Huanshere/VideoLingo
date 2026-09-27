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
