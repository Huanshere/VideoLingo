"""Subtitle lines are split by how wide they are drawn (core/_5_split_sub.py), not by how many characters they have."""
import pytest

import core._5_split_sub as split_sub
from core._5_split_sub import SOURCE, TRANSLATION, line_width, uses_cjk_font


def _settings(monkeypatch, max_length=80, multiplier=1.0):
    settings = {"subtitle": {"max_length": max_length, "target_multiplier": multiplier}, "max_workers": 2}
    monkeypatch.setattr(split_sub, "load_key", lambda key: settings[key])


def _too_long(src, tr):
    return split_sub.length_check([src], [tr])(src, tr)


# ------------------------------------------------------------------
# How wide a line is drawn
# ------------------------------------------------------------------

def test_a_row_is_80_latin_letters_wide():
    for row in (TRANSLATION, SOURCE):
        assert line_width("a" * 80, row, cjk_font=False) == 80


@pytest.mark.parametrize("text,translation,source", [
    ("中文字幕", 4 * 2.84, 4 * 2.27),
    ("ひらがなカタカナ", 8 * 2.79, 8 * 2.27),
    ("한국어자막", 5 * 2.57, 5 * 2.11),
    ("ภาษาไทย", 7 * 1.13, 7 * 1.05),
    ("Русский", 7 * 1.14, 7 * 1.13),
    ("हिन्दी", 6 * 1.15, 6 * 1.05),
])
def test_each_script_has_its_own_width(text, translation, source):
    cjk_font = uses_cjk_font([text])
    assert line_width(text, TRANSLATION, cjk_font) == pytest.approx(translation)
    assert line_width(text, SOURCE, cjk_font) == pytest.approx(source)


def test_latin_in_a_cjk_font_is_wider_and_its_spaces_narrower():
    assert line_width("Brendan Eich", TRANSLATION, cjk_font=False) == 12
    assert line_width("Brendan Eich", TRANSLATION, cjk_font=True) == pytest.approx(11 * 1.5 + 0.85)
    assert line_width("Brendan Eich", SOURCE, cjk_font=True) == pytest.approx(11 * 1.2 + 0.7)


@pytest.mark.parametrize("lines,expected", [
    (["JavaScript 是在十天之内创造出来的", "由 Brendan Eich 设计"], True),
    (["The word 你好 means hello in Chinese."], False),
    (["1995년 브렌던 아이크가 단 열흘 만에 만들었습니다"], True),
    (["1995 年にブレンダン・アイクが作りました"], True),
    (["Сегодня он работает на миллиардах устройств"], False),
    (["123 !?", "♪♪"], False),
    ([], False),
])
def test_a_track_is_in_a_cjk_font_when_most_of_what_it_says_is_cjk(lines, expected):
    assert uses_cjk_font(lines) is expected


def test_the_split_and_the_typesetter_agree_on_the_font():
    typeset = pytest.importorskip("core.utils.typeset")
    for lines in (
        ["JavaScript 是在十天之内创造出来的", "由 Brendan Eich 设计"],
        ["The word 你好 means hello in Chinese."],
        ["1995년 브렌던 아이크가 단 열흘 만에 만들었습니다"],
        ["1995 年にブレンダン・アイクが作りました"],
        ["佢係 Brendan Eich 喺 1995 年淨係用咗十日整出嚟嘅"],
        ["มันถูกสร้างขึ้นในปี 1995 โดยเบรนแดน ไอค์"],
    ):
        assert uses_cjk_font(lines) == (typeset.classify(lines) in {"zh", "ja", "ko"}), lines


def _drawn_width(typeset, text, role):
    """Width of `text` on one row as the typesetter draws it, in units of 1/80 of a landscape row."""
    wide = typeset.geometry(40000, 480)  # the same type size, and room enough that nothing is broken or tightened
    block = typeset.typeset_cue(typeset.Cue(0, 1000, text), typeset.plan_track(role, [text]), wide)
    (line,) = block.lines
    factor, scale = block.squeeze
    width = 0.0
    for index, token in enumerate(line):
        if index and token.space_before:
            width += scale * (token.gap_glyphs + factor * token.gap_spacing)
        width += scale * (token.glyphs + factor * token.spacing)
    return width * wide.unit / (typeset.geometry(854, 480).max_width / 80)


@pytest.mark.parametrize("text", [
    "如今它运行在全世界数十亿台各种各样的设备上从网页浏览器到服务器甚至再到我们每个人口袋里的智能手机",
    "如今它運行在全世界數十億台各式各樣的裝置上從網頁瀏覽器到伺服器甚至再到我們每個人口袋裡的智慧型手機",
    "いまではせかいじゅうのウェブブラウザからサーバーそしてわたしたちのポケットのなかのスマートフォンまで",
    "오늘날에는전세계의웹브라우저부터서버그리고우리주머니속스마트폰까지수십억대의다양한기기에서실행되고있습니다",
])
def test_the_widths_are_those_the_typesetter_draws(text):
    typeset = pytest.importorskip("core.utils.typeset")
    from core.utils import subtitle_fonts

    if subtitle_fonts.missing([typeset.track_family(typeset.MAIN, [text])]):
        pytest.skip("the Chinese and Japanese faces are downloaded on first use")
    cjk_font = uses_cjk_font([text])
    for row, role in ((TRANSLATION, typeset.MAIN), (SOURCE, typeset.SECONDARY)):
        assert line_width(text, row, cjk_font) == pytest.approx(_drawn_width(typeset, text, role), rel=0.02)


# ------------------------------------------------------------------
# Which lines are split
# ------------------------------------------------------------------

@pytest.mark.parametrize("src,tr,expected", [
    ("a" * 80, "短", False),
    ("a" * 81, "短", True),
    ("中" * 35, "short", False),                  # a Chinese source row holds 35 ideographs
    ("中" * 36, "short", True),
    ("한" * 37, "short", False),
    ("한" * 38, "short", True),
    ("short", "中" * 46, False),                  # a Chinese translation reads well as two rows of 23
    ("short", "中" * 47, True),
    ("short", "中" * 46 + "。", False),           # shown without the full stop
    ("short", "中" * 23 + "，" + "中" * 23, False),  # nor its commas: a narrow space instead
    ("short", "か" * 47, False),
    ("short", "か" * 48, True),
    ("short", "a" * 130, False),
    ("short", "a" * 135, True),
])
def test_a_line_is_split_when_it_is_drawn_too_wide(monkeypatch, src, tr, expected):
    _settings(monkeypatch)
    assert _too_long(src, tr) is expected


def test_max_length_and_target_multiplier_still_apply(monkeypatch):
    _settings(monkeypatch, max_length=40)
    assert _too_long("a" * 40, "短") is False
    assert _too_long("a" * 41, "短") is True
    _settings(monkeypatch, multiplier=1.2)
    assert _too_long("a" * 80, "中" * 38) is False  # the multiplier is for the translation only
    assert _too_long("a" * 80, "中" * 39) is True


def test_source_lines_without_a_translation_are_split_by_width(monkeypatch):
    _settings(monkeypatch)
    monkeypatch.setattr(split_sub, "check_cancel", lambda: None)
    asked = []

    def split_sentence(sentence, num_parts):
        asked.append(sentence)
        words = sentence.split(" ") if " " in sentence else list(sentence)
        joiner, middle = (" " if " " in sentence else ""), len(words) // 2
        return joiner.join(words[:middle]) + "\n" + joiner.join(words[middle:])

    monkeypatch.setattr(split_sub, "split_sentence", split_sentence)

    assert split_sub.split_source_lines(["中" * 35, "中" * 36]) == ["中" * 35, "中" * 18, "中" * 18]
    assert asked == ["中" * 36]

    english = " ".join(["word"] * 16)  # 79 letters and spaces
    assert split_sub.split_source_lines([english]) == [english]
    longer = english + " x"
    assert split_sub.split_source_lines([longer]) == [" ".join(["word"] * 8), " ".join(["word"] * 8 + ["x"])]

    # A very long line is split again until it fits, three times at most
    lines = split_sub.split_source_lines(["中" * 150])
    assert "".join(lines) == "中" * 150
    assert all(line_width(line, SOURCE, cjk_font=True) <= 80 for line in lines)
    assert len(lines) == 8
