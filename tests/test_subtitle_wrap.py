"""Long lines broken before the plain `subtitles` filter draws them (core/utils/subtitle_width.py).

The filter breaks a line at its spaces only, so a long Chinese, Japanese or Thai line would run
off both sides of the frame.
"""
import unicodedata

import pytest

from core.utils.subtitle_width import (CLOSING, FOLLOWING_VOWELS, LEADING_VOWELS, OPENING, SOURCE,
                                       line_width, plain_row_capacity, wrap_line, wrap_srt)

LANDSCAPE = plain_row_capacity(1920, 1080, 17)
PORTRAIT = plain_row_capacity(1080, 1920, 17)

LONG = {
    "zh": "如今它运行在全世界数十亿台设备上，从网页浏览器、服务器，一直到你口袋里的智能手机。还有更多的地方。",
    "ja": "JavaScript は 1995 年、ブレンダン・アイクがわずか 10 日間で作りました。それから「ウェブの言語」と呼ばれるようになりました。",
    "th": "JavaScript ถูกสร้างขึ้นโดยเบรนแดน ไอค์ ในเวลาเพียงสิบวันเมื่อปี 1995 และปัจจุบันมันทำงานอยู่บนอุปกรณ์หลายพันล้านเครื่องทั่วโลก",
    "zh-unbroken": "这是一句非常非常长的中文字幕它没有任何标点符号也没有空格只是一直在说话说个不停直到画面的尽头还没有结束",
}


def _width(row):
    return line_width(row, SOURCE, True)


def _rows(text, capacity):
    return wrap_line(text, capacity).split("\n")


# ------------
# One line
# ------------

def test_the_plain_row_holds_less_on_a_portrait_frame_and_at_a_larger_size():
    assert LANDSCAPE == pytest.approx(80)
    assert PORTRAIT == pytest.approx(80 * (9 / 16) ** 2)
    assert plain_row_capacity(1920, 1080, 34) == pytest.approx(40)


@pytest.mark.parametrize("capacity", [LANDSCAPE, PORTRAIT], ids=["landscape", "portrait"])
@pytest.mark.parametrize("language", list(LONG))
def test_a_long_line_is_broken_into_rows_that_fit(language, capacity):
    text = LONG[language]
    rows = _rows(text, capacity)
    assert len(rows) > 1
    assert all(_width(row) <= capacity for row in rows), rows
    assert "".join(rows).replace(" ", "") == text.replace(" ", "")  # nothing lost or added
    widths = [_width(row) for row in rows]
    assert max(widths) - min(widths) < capacity / 2, rows  # balanced, not filled up


def test_chinese_breaks_at_a_comma():
    rows = _rows(LONG["zh"][:41], LANDSCAPE)  # "...智能手机。" in two rows
    assert len(rows) == 2 and rows[0][-1] in "，、", rows


def test_no_row_starts_with_closing_punctuation_or_ends_with_an_opening_one():
    for language in ("zh", "ja"):
        for capacity in (LANDSCAPE, PORTRAIT, 20):
            for row in _rows(LONG[language], capacity):
                assert row[0] not in CLOSING and row[-1] not in OPENING, (language, capacity, row)


def test_thai_rows_keep_vowels_and_marks_with_their_consonant():
    for capacity in (LANDSCAPE, PORTRAIT, 20):
        rows = _rows(LONG["th"], capacity)
        for row in rows[1:]:
            assert row[0] not in FOLLOWING_VOWELS and unicodedata.category(row[0])[0] != "M", row
        for row in rows[:-1]:
            assert row[-1] not in LEADING_VOWELS, row


@pytest.mark.parametrize("text", [
    "Today it runs on billions of devices, from browsers to servers to the phone in your pocket and beyond.",
    "जावास्क्रिप्ट को ब्रेंडन आइक ने 1995 में सिर्फ़ दस दिनों में बनाया था और आज यह अरबों उपकरणों पर चलती है।",
    "Сегодня он работает на миллиардах устройств, от браузеров и серверов до телефона в вашем кармане.",
])
def test_lines_the_filter_breaks_at_their_spaces_are_left_to_it(text):
    assert wrap_line(text, PORTRAIT) == text


def test_a_line_that_fits_is_left_as_it_is():
    text = "JavaScript 是 Brendan Eich 在 1995 年仅用十天创造出来的。"
    assert _width(text) < LANDSCAPE
    assert wrap_line(text, LANDSCAPE) == text


def test_however_long_a_line_every_row_stays_on_the_frame():
    rows = _rows("中文" * 200, LANDSCAPE)
    assert len(rows) >= 400 * 2.27 / LANDSCAPE
    assert all(_width(row) <= LANDSCAPE for row in rows)


# ------------
# SRT files
# ------------

SRT = (
    "1\r\n00:00:00,000 --> 00:00:02,000\r\nShort.\r\n\r\n"
    "2\r\n00:00:02,000 --> 00:00:04,000\r\n" + LONG["zh"] + "\r\n\r\n"
)


def test_only_the_text_of_the_cues_is_broken():
    wrapped = wrap_srt(SRT, LANDSCAPE)
    blocks = wrapped.split("\n\n")
    assert blocks[0] == "1\n00:00:00,000 --> 00:00:02,000\nShort."
    lines = blocks[1].split("\n")
    assert lines[:2] == ["2", "00:00:02,000 --> 00:00:04,000"]
    assert "".join(lines[2:]) == LONG["zh"]
    assert len(lines) > 3
    assert wrapped.endswith("\n") and "\r" not in wrapped


def test_a_file_without_long_lines_is_not_rewritten():
    assert wrap_srt("1\n00:00:00,000 --> 00:00:02,000\n短的。\n", LANDSCAPE) is None
    assert wrap_srt("", LANDSCAPE) is None
