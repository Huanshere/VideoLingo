"""Fetching the Chinese and Japanese subtitle faces (core/utils/subtitle_fonts.py), without a network."""
import hashlib
import os
import sys
from types import SimpleNamespace

import pytest
import requests

pytest.importorskip("fontTools", reason="the subtitle fonts are built with fontTools (requirements.txt)")

from core.task_runner import StopTask  # noqa: E402
from core.utils import subtitle_fonts  # noqa: E402

FONT = b"the upstream variable font"
JP, SC = "Noto Sans JP Book", "Noto Sans SC Book"


class Response:
    def __init__(self, body):
        self.body = body
        self.headers = {"Content-Length": str(len(body))}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def raise_for_status(self):
        pass

    def iter_content(self, size):
        for start in range(0, len(self.body), size):
            yield self.body[start:start + size]


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


@pytest.fixture
def fonts(tmp_path, monkeypatch):
    """An empty fonts/ (`.dir`), mirrors answered by `.answers` (url -> bytes, a response maker or an exception), a fake clock."""
    monkeypatch.setattr(subtitle_fonts, "FONTS_DIR", str(tmp_path))
    monkeypatch.setattr(subtitle_fonts, "_FAILED", {})
    monkeypatch.setattr(subtitle_fonts, "check_cancel", lambda: None)
    digest = hashlib.sha256(FONT).hexdigest()
    monkeypatch.setattr(subtitle_fonts, "DOWNLOADS", {
        JP: ("notosansjp/jp.ttf", digest, "Noto Sans JP"),
        SC: ("notosanssc/sc.ttf", digest, "Noto Sans SC"),
    })

    class Built:
        def __init__(self, source):
            with open(source, "rb") as handle:
                self.data = handle.read()

        def save(self, path):
            with open(path, "wb") as handle:
                handle.write(b"built from " + self.data)

    monkeypatch.setattr(subtitle_fonts, "book", lambda source, family, stem: Built(source))
    clock = Clock()
    monkeypatch.setattr(subtitle_fonts.time, "monotonic", clock)
    asked, answers = [], {}

    def get(url, **kwargs):
        asked.append(url)
        answer = answers.get(url, requests.ConnectionError("unreachable"))
        if isinstance(answer, BaseException):
            raise answer
        return answer(clock) if callable(answer) else Response(answer)

    monkeypatch.setattr(subtitle_fonts.requests, "get", get)
    return SimpleNamespace(dir=tmp_path, asked=asked, answers=answers, clock=clock)


def _url(mirror, family=JP):
    return subtitle_fonts.MIRRORS[mirror].format(commit=subtitle_fonts.GOOGLE_FONTS_COMMIT,
                                                 path=subtitle_fonts.DOWNLOADS[family][0])


def _saved(fonts):
    return sorted(os.listdir(fonts.dir))


def test_every_mirror_is_tried_until_one_gives_the_expected_file(fonts):
    fonts.answers[_url(1)] = b"a page that is not the font"
    fonts.answers[_url(2)] = FONT
    assert subtitle_fonts.fetch(JP)
    assert fonts.asked == [_url(0), _url(1), _url(2)]
    assert _saved(fonts) == ["NotoSansJP-Book.ttf"]  # nothing half-written is left
    assert (fonts.dir / "NotoSansJP-Book.ttf").read_bytes() == b"built from " + FONT
    if sys.platform != "win32":
        assert (fonts.dir / "NotoSansJP-Book.ttf").stat().st_mode & 0o777 == 0o644


def test_a_file_larger_than_expected_is_not_downloaded_to_the_end(fonts, monkeypatch):
    monkeypatch.setattr(subtitle_fonts, "MAX_BYTES", 10)
    for mirror in range(len(subtitle_fonts.MIRRORS)):
        fonts.answers[_url(mirror)] = FONT
    assert not subtitle_fonts.fetch(JP)
    assert _saved(fonts) == []


def test_a_slow_download_is_given_up_after_the_deadline(fonts):
    def slow(clock):
        response = Response(FONT)
        chunks = response.iter_content

        def iter_content(size):
            for chunk in chunks(4):
                clock.now += subtitle_fonts.DEADLINE / 3
                yield chunk

        response.iter_content = iter_content
        return response

    for mirror in range(len(subtitle_fonts.MIRRORS)):
        fonts.answers[_url(mirror)] = slow
    assert not subtitle_fonts.fetch(JP)
    assert fonts.asked == [_url(0)]  # no time left for the other mirrors
    assert _saved(fonts) == []


def test_a_family_that_could_not_be_downloaded_is_not_tried_again_at_once(fonts):
    assert not subtitle_fonts.fetch(JP)
    tried = len(fonts.asked)
    assert tried == len(subtitle_fonts.MIRRORS)
    fonts.clock.now += subtitle_fonts.RETRY_AFTER - 1
    assert not subtitle_fonts.fetch(JP)  # the next video of a batch does not wait for it again
    assert len(fonts.asked) == tried
    fonts.clock.now += 2
    fonts.answers[_url(0)] = FONT
    assert subtitle_fonts.fetch(JP)
    assert len(fonts.asked) == tried + 1


def test_ensure_stops_at_the_first_family_that_can_not_be_had(fonts):
    assert not subtitle_fonts.ensure([JP, SC])
    assert all("notosansjp" in url for url in fonts.asked)


def test_stopping_the_task_stops_the_download(fonts, monkeypatch):
    def stop():
        raise StopTask()

    monkeypatch.setattr(subtitle_fonts, "check_cancel", stop)
    fonts.answers[_url(0)] = FONT
    with pytest.raises(StopTask):
        subtitle_fonts.fetch(JP)
    assert _saved(fonts) == []


def test_a_font_that_can_not_be_built_leaves_nothing_behind(fonts, monkeypatch):
    def broken(source, family, stem):
        raise ValueError("not a font")

    monkeypatch.setattr(subtitle_fonts, "book", broken)
    fonts.answers[_url(0)] = FONT
    assert not subtitle_fonts.fetch(JP)
    assert _saved(fonts) == []


# ------------
# A variable font put in fonts/ by hand
# ------------

def _variable_font(family, axis="wght"):
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.ttGlyphPen import TTGlyphPen

    builder = FontBuilder(1000, isTTF=True)
    builder.setupGlyphOrder([".notdef", "A"])
    builder.setupCharacterMap({0x41: "A"})
    pen = TTGlyphPen(None)
    pen.moveTo((0, 0))
    pen.lineTo((0, 500))
    pen.lineTo((500, 0))
    pen.closePath()
    builder.setupGlyf({".notdef": pen.glyph(), "A": pen.glyph()})
    builder.setupHorizontalMetrics({".notdef": (500, 0), "A": (500, 0)})
    builder.setupHorizontalHeader(ascent=800, descent=-200)
    builder.setupNameTable({"familyName": family, "styleName": "Regular"})
    builder.setupOS2()
    builder.setupPost()
    builder.setupFvar(axes=[(axis, 100, 400, 900, "Axis")], instances=[])
    return builder.font


@pytest.mark.parametrize("name", ["NotoSansJP[wght].ttf", "NotoSansJP-VariableFont_wght.ttf"])
def test_a_variable_font_put_in_fonts_is_used_without_a_network(fonts, monkeypatch, name):
    from fontTools.ttLib import TTFont

    monkeypatch.undo()  # the real files and recipe, but still no network
    monkeypatch.setattr(subtitle_fonts, "FONTS_DIR", str(fonts.dir))
    monkeypatch.setattr(subtitle_fonts.requests, "get", lambda *args, **kwargs: pytest.fail("downloaded"))
    _variable_font("Noto Sans JP").save(fonts.dir / name)
    assert subtitle_fonts.fetch(JP)
    assert _saved(fonts) == sorted([name, "NotoSansJP-Book.ttf"])
    built = TTFont(fonts.dir / "NotoSansJP-Book.ttf")
    assert built["name"].getDebugName(1) == JP
    assert "fvar" not in built and built["OS/2"].usWeightClass == subtitle_fonts.BOOK_WEIGHT


@pytest.mark.parametrize("font", [lambda: _variable_font("Noto Sans SC"), lambda: _variable_font("Noto Sans JP", "wdth")])
def test_another_font_put_in_fonts_is_not_used(fonts, font):
    font().save(fonts.dir / "NotoSansJP[wght].ttf")
    assert subtitle_fonts.local_source(JP) is None
    assert not subtitle_fonts.fetch(JP)  # it goes on to download the font
    assert len(fonts.asked) == len(subtitle_fonts.MIRRORS)
