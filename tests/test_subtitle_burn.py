"""Which ffmpeg filter burns the subtitles (core/utils/subtitle_style.py), and the plain one when the typesetter can not be used."""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import core.utils
from core.utils import subtitle_style

SOURCE_SRT = "1\n00:00:00,000 --> 00:00:02,000\nJavaScript was created in just ten days.\n"
# Latin on both rows: set in the fonts of the repository, nothing is downloaded
TRANSLATION_SRT = "1\n00:00:00,000 --> 00:00:02,000\nJavaScript se creó en solo diez días.\n"


def _config(monkeypatch, font_name=""):
    style = {kind: dict(values, font_name=font_name) for kind, values in subtitle_style.DEFAULT_STYLE.items()}
    settings = {"subtitle.style": style}
    monkeypatch.setattr(subtitle_style, "load_key_or", lambda key, default: settings.get(key, default))


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("output").mkdir()
    Path("output/src.srt").write_text(SOURCE_SRT, encoding="utf-8")
    Path("output/trans.srt").write_text(TRANSLATION_SRT, encoding="utf-8")
    return tmp_path


def _candidates():
    return subtitle_style.get_subtitle_filter_candidates("subtitle", "output/src.srt", "output/trans.srt", 1920, 1080)


def _plain():
    return subtitle_style.get_subtitle_filters("subtitle", "output/src.srt", "output/trans.srt", width=1920, height=1080)


def _typesetter():
    pytest.importorskip("uharfbuzz", reason="the subtitle typesetter needs uharfbuzz (requirements.txt)")
    from core.utils import typeset

    if os.path.splitdrive(os.getcwd())[0].lower() != os.path.splitdrive(typeset.FONTS_DIR)[0].lower():
        pytest.skip("fonts/ is on another drive than the temporary folder")
    return typeset


# ------------
# The filters
# ------------

def test_without_a_font_name_the_typesetter_burns_them_first(workspace, monkeypatch):
    typeset = _typesetter()
    _config(monkeypatch)
    stale = Path("output/ass/subtitle/stale.ass")
    stale.parent.mkdir(parents=True)
    stale.write_text("", encoding="utf-8")

    typeset_filters, plain_filters = _candidates()
    assert plain_filters == _plain()
    assert not stale.exists()  # the scripts of an earlier run are not burnt in
    parts = typeset_filters.split(",")
    assert parts
    for part in parts:
        match = re.fullmatch(r"ass=(output/ass/subtitle/[\w.-]+\.ass):fontsdir=([\w./+-]+):shaping=\w+", part)
        assert match, part
        assert Path(match[1]).is_file()
        assert Path(match[2]).resolve() == Path(typeset.FONTS_DIR).resolve()


def test_a_font_of_the_users_choice_is_burnt_with_the_subtitles_filter(workspace, monkeypatch):
    _config(monkeypatch, font_name="Arial")
    assert _candidates() == [_plain()]
    assert "FontName=Arial" in _plain()
    assert not Path("output/ass").exists()


def test_without_the_typesetting_libraries_the_subtitles_filter_burns_them(workspace, monkeypatch):
    _config(monkeypatch)
    for name in ("typeset", "subtitle_fonts"):
        monkeypatch.delattr(core.utils, name, raising=False)
        monkeypatch.setitem(sys.modules, f"core.utils.{name}", None)  # makes the import raise ImportError
    assert _candidates() == [_plain()]


def test_a_font_that_can_not_be_downloaded_falls_back_to_the_subtitles_filter(workspace, monkeypatch):
    _typesetter()
    from core.utils import subtitle_fonts

    _config(monkeypatch)
    asked = []
    monkeypatch.setattr(subtitle_fonts, "ensure", lambda families: asked.append(families) or False)
    assert _candidates() == [_plain()]
    assert asked == [["VL Roboto Cond Sub", "VL Noto Sans XCond Main"]]


def test_a_typesetter_error_falls_back_to_the_subtitles_filter(workspace, monkeypatch):
    typeset = _typesetter()

    def broken(*args, **kwargs):
        raise RuntimeError("broken")

    _config(monkeypatch)
    monkeypatch.setattr(typeset, "build_scripts", broken)
    assert _candidates() == [_plain()]


def test_a_frame_of_unknown_size_is_burnt_with_the_plain_filter_as_it_is(workspace, monkeypatch):
    _config(monkeypatch)
    filters = subtitle_style.get_subtitle_filter_candidates("subtitle", "output/src.srt", "output/trans.srt", 0, 0)
    assert filters == [subtitle_style.get_subtitle_filters("subtitle", "output/src.srt", "output/trans.srt")]
    assert "subtitles=output/trans.srt:" in filters[0]
    assert not Path("output/ass").exists()


def test_stopping_the_task_while_a_font_downloads_stops_it(workspace, monkeypatch):
    _typesetter()
    from core.task_runner import StopTask
    from core.utils import subtitle_fonts

    def stopped(families):
        raise StopTask()

    _config(monkeypatch)
    monkeypatch.setattr(subtitle_fonts, "ensure", stopped)
    with pytest.raises(StopTask):
        _candidates()


# ------------
# The plain filter
# ------------

LONG_TRANSLATION = "如今它运行在全世界数十亿台设备上，从网页浏览器、服务器，一直到你口袋里的智能手机。"


def test_the_plain_filter_burns_long_chinese_lines_broken(workspace, monkeypatch):
    _config(monkeypatch, font_name="Arial")
    Path("output/trans.srt").write_text("\ufeff" + TRANSLATION_SRT.replace("JavaScript se creó en solo diez días.", LONG_TRANSLATION),
                                        encoding="utf-8")
    [filters] = _candidates()
    assert filters.startswith("subtitles=output/src.srt:")  # the English line is left to the filter
    assert ",subtitles=output/ass/subtitle/plain_translation.srt:" in filters
    lines = Path("output/ass/subtitle/plain_translation.srt").read_text(encoding="utf-8").split("\n")
    assert lines[:2] == ["1", "00:00:00,000 --> 00:00:02,000"]
    assert lines[2:4] == ["如今它运行在全世界数十亿台设备上，", "从网页浏览器、服务器，一直到你口袋里的智能手机。"]


def test_a_portrait_frame_breaks_them_into_more_rows(workspace, monkeypatch):
    _config(monkeypatch, font_name="Arial")
    Path("output/trans.srt").write_text(TRANSLATION_SRT.replace("JavaScript se creó en solo diez días.", LONG_TRANSLATION),
                                        encoding="utf-8")
    subtitle_style.get_subtitle_filter_candidates("subtitle", "output/src.srt", "output/trans.srt", 1080, 1920)
    text = Path("output/ass/subtitle/plain_translation.srt").read_text(encoding="utf-8").split("\n")[2:]
    assert len([line for line in text if line]) >= 4


def test_an_srt_that_can_not_be_read_is_burnt_as_it_is(workspace, monkeypatch):
    _config(monkeypatch, font_name="Arial")
    Path("output/trans.srt").write_bytes(b"\xff\xfe\x00broken")
    assert subtitle_style.get_plain_srt("subtitle", "translation", "output/trans.srt", 1920, 1080) == "output/trans.srt"


# ------------
# Burning them with ffmpeg
# ------------

def _burn(monkeypatch, candidates=None):
    """Run core/_7_sub_into_vid.py on a black clip; returns the -vf of every ffmpeg run."""
    from core import _1_ytdlp, _7_sub_into_vid as merge

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("FFmpeg and FFprobe are required")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                    "-i", "color=c=black:s=320x240:r=25:d=2", "-c:v", "mpeg4", "output/source.mp4"], check=True)
    monkeypatch.setattr(_1_ytdlp, "is_audio_only_input", lambda: False)
    monkeypatch.setattr(merge, "find_video_files", lambda: "output/source.mp4")
    monkeypatch.setattr(merge, "load_key", {"burn_subtitles": True, "ffmpeg_gpu": False}.__getitem__)
    monkeypatch.setattr(merge, "check_cancel", lambda: None)
    if candidates is not None:
        monkeypatch.setattr(merge, "get_subtitle_filter_candidates", lambda *args: candidates)
    filters, popen = [], subprocess.Popen

    def recording_popen(command, *args, **kwargs):
        if "-vf" in command:  # subprocess.run starts its processes through Popen too
            filters.append(command[command.index("-vf") + 1].decode("utf-8"))
        return popen(command, *args, **kwargs)

    monkeypatch.setattr(merge.subprocess, "Popen", recording_popen)
    merge.merge_subtitles_to_video()
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-of", "json", merge.OUTPUT_VIDEO],
                           check=True, capture_output=True, text=True)
    assert [stream["codec_type"] for stream in json.loads(probe.stdout)["streams"]] == ["video"]
    return filters


def test_an_ffmpeg_that_can_not_burn_the_typeset_subtitles_burns_the_plain_ones(workspace, monkeypatch):
    plain = "null"  # stands in for the subtitles filter, which needs libass as well
    # As an ffmpeg that can not run the `ass` filter answers
    filters = _burn(monkeypatch, ["vl_no_such_filter=output/x.ass", plain])
    assert [f.split(",")[-1] for f in filters] == ["vl_no_such_filter=output/x.ass", plain]


def test_a_failure_of_every_filter_is_reported(workspace, monkeypatch):
    with pytest.raises(subprocess.CalledProcessError):
        _burn(monkeypatch, ["vl_no_such_filter=a", "vl_no_such_filter=b"])


def test_the_typeset_subtitles_are_burnt_with_real_ffmpeg(workspace, monkeypatch):
    _typesetter()
    if not shutil.which("ffmpeg"):
        pytest.skip("FFmpeg is required")
    listed = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    if not re.search(r"^\s*\S+\s+ass\s", listed, re.MULTILINE):
        pytest.skip("needs an ffmpeg with libass (python installer.py installs one)")
    _config(monkeypatch)
    filters = _burn(monkeypatch)
    assert len(filters) == 1 and ",ass=output/ass/subtitle/" in filters[0]
