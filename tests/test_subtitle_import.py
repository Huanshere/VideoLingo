"""Regression tests for timestamp-like dialogue in imported SRT files."""
import pytest

from core._2_import_subtitles import read_cues


@pytest.mark.parametrize("encoding", ["utf-8", "utf-8-sig", "utf-16"])
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_timestamp_inside_dialogue_is_not_a_cue(encoding, newline):
    dialogue = "The example 00:00:03,000 --> 00:00:04,000 is part of this caption."
    subtitle = (
        "1\n00:00:01,000 --> 00:00:02,000\n"
        f"{dialogue}\n\n"
        "2\n00:00:05,000 --> 00:00:06,000\nNext caption.\n"
    )

    assert read_cues(subtitle.replace("\n", newline).encode(encoding)) == [
        (1.0, 2.0, dialogue),
        (5.0, 6.0, "Next caption."),
    ]


@pytest.mark.parametrize("prefix", ["", " ", "\t"])
def test_indented_timing_line_with_coordinates(prefix):
    subtitle = (
        f"1\n{prefix}00:00:01,000 --> 00:00:02,000 X1:0 X2:100 Y1:0 Y2:100\n"
        "Hello world.\n"
    )

    assert read_cues(subtitle.encode()) == [(1.0, 2.0, "Hello world.")]
