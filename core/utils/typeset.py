"""Bilingual subtitle typesetter.

Turns the source and the translated SRT into ASS scripts written at the real
output resolution. A font and a size are chosen per writing system, every line
is measured here and broken here (libass cannot break Chinese, Japanese or
Thai by itself), and the translation is stacked on the original explicitly so
the two tracks never overlap.

Units: one "golden unit" is frame_short_side / 288, the grid of the 384x288
scripts the `subtitles` filter writes for an SRT (FontSize 17 over 15 by
default). libass scales a face so that usWinAscent + usWinDescent equals
FontSize, so equal FontSize does not mean equal visible size: STYLES holds a
size per script, set by eye against the English + Chinese pair. The colours,
the outline and a size factor come from `subtitle.style` in config.yaml (see
`Look`).

Shaping: ffmpeg's `subtitles` filter always runs libass with the simple shaper,
which cannot set Indic conjuncts, Thai marks or Arabic properly. The scripts
written here are burnt with the `ass` filter instead, one script per shaping
mode: cues with a complex script go through HarfBuzz, everything else keeps the
simple shaper.

Fonts: the faces are found by family name through `ass=...:fontsdir=fonts`,
nothing has to be installed. The Chinese and Japanese faces are too big for the
repository and are fetched on first use by `subtitle_fonts.py`; fonts/README.md
says where every face comes from.
"""
from __future__ import annotations

import bisect
import functools
import os
import re
import struct
import sys
import unicodedata
from dataclasses import dataclass, field, replace

import uharfbuzz as hb

FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "fonts")

MAIN = "main"            # translation: yellow on a translucent box, upper block
SECONDARY = "secondary"  # original speech: white with an outline, bottom block

SIMPLE = "simple"
COMPLEX = "complex"

# ---------------------------------------------------------------- fonts ----


@dataclass(frozen=True)
class Style:
    family: str           # the name libass finds the face by
    size: float           # FontSize in golden units
    spacing: float = 0.0  # letter spacing in golden units
    scale_x: float = 1.0  # horizontal scale (ASS ScaleX / 100)


# Family name -> file in fonts/. Static faces only: libass renders the default
# instance of a variable font and nothing else.
FONT_FILES = {
    "VL Noto Sans XCond Main": "VLNotoSansXCondMain.ttf",
    "VL Roboto Cond Sub": "VLRobotoCondSub.ttf",
    "Noto Sans SC Book": "NotoSansSC-Book.ttf",
    "Noto Sans TC Book": "NotoSansTC-Book.ttf",
    "Noto Sans HK Book": "NotoSansHK-Book.ttf",
    "Noto Sans JP Book": "NotoSansJP-Book.ttf",
    "Pretendard Medium": "Pretendard-Medium.otf",
}

STYLES = {
    MAIN: {
        "latin": Style("VL Noto Sans XCond Main", 22),
        "zh": Style("Noto Sans SC Book", 23.7, 0.9),
        "zh-hant": Style("Noto Sans TC Book", 23.7, 0.9),
        "yue": Style("Noto Sans HK Book", 23.7, 0.9),
        "ja": Style("Noto Sans JP Book", 23.8, 0.5),
        "ko": Style("Pretendard Medium", 21.2, 0.25),
    },
    SECONDARY: {
        "latin": Style("VL Roboto Cond Sub", 18, 0.0, 0.96),
        # The face for what "latin" cannot set (Central European, Turkish,
        # Vietnamese, Cyrillic, Greek). Roboto sets them all, so it is the same.
        "latin+": Style("VL Roboto Cond Sub", 18, 0.0, 0.96),
        "zh": Style("Noto Sans SC Book", 19.4, 0.4),
        "zh-hant": Style("Noto Sans TC Book", 19.4, 0.4),
        "yue": Style("Noto Sans HK Book", 19.4, 0.4),
        "ja": Style("Noto Sans JP Book", 19.4, 0.4),
        "ko": Style("Pretendard Medium", 17.3, 0.25),
    },
}

# Long-tail source scripts: class -> (font name suffix, secondary FontSize).
# Every size gives the same visible size as the golden English secondary.
_LONG_TAIL = {
    "thai": ("Thai", 23.36), "devanagari": ("Devanagari", 20.84), "arabic": ("Arabic", 25.79),
    "hebrew": ("Hebrew", 18.05), "bengali": ("Bengali", 20.85), "tamil": ("Tamil", 20.07),
    "telugu": ("Telugu", 22.69), "kannada": ("Kannada", 21.87), "malayalam": ("Malayalam", 20.07),
    "gujarati": ("Gujarati", 21.39), "gurmukhi": ("Gurmukhi", 21.14), "oriya": ("Oriya", 21.85),
    "sinhala": ("Sinhala", 21.07), "khmer": ("Khmer", 26.40), "lao": ("Lao", 25.86),
    "myanmar": ("Myanmar", 26.21),
}
MAIN_OVER_SECONDARY = 1.075  # how much bigger the same face is set as the main track
for _cls, (_suffix, _size) in _LONG_TAIL.items():
    FONT_FILES[f"VL Noto Sans {_suffix}"] = f"VLNotoSans{_suffix}-Medium.ttf"
    STYLES[SECONDARY][_cls] = Style(f"VL Noto Sans {_suffix}", _size)
    STYLES[MAIN][_cls] = Style(f"VL Noto Sans {_suffix}", round(_size * MAIN_OVER_SECONDARY, 2))

# Classes without a style of their own use another class's.
STYLE_FALLBACK = {
    MAIN: {"cyrillic": "latin", "greek": "latin", "zh-hant": "zh", "yue": "zh-hant"},
    SECONDARY: {"cyrillic": "latin+", "greek": "latin+", "zh-hant": "zh", "yue": "zh-hant"},
}
# Where a character is looked for when the track's own face cannot set it.
FALLBACK_KEYS = ["latin", "latin+", "zh", "zh-hant", "yue", "ja", "ko"]
HAN_KEYS = ["zh", "zh-hant", "yue", "ja"]


class FontFace:
    def __init__(self, family, path):
        self.family = family
        self.path = path
        self.hb_face = hb.Face(hb.Blob.from_file_path(path))
        self.hb_font = hb.Font(self.hb_face)
        ascent, descent = _win_metrics(self.hb_face)
        self.height_units = ascent + descent      # what libass maps to FontSize
        self.ascent = ascent / self.height_units  # share of FontSize above the baseline
        self.descent = descent / self.height_units
        self.em = self.hb_face.upem / self.height_units  # em per FontSize unit
        self._glyphs = {}
        self._shaped = {}

    def _glyph(self, char):
        hit = self._glyphs.get(char)
        if hit is None:
            glyph = self.hb_font.get_nominal_glyph(ord(char))
            if glyph:
                hit = (True, self.hb_font.get_glyph_h_advance(glyph) / self.height_units)
            else:
                # Not in this face: libass will take it from a system font. Guess a width.
                wide = unicodedata.east_asian_width(char) in "WF"
                hit = (False, (1.0 if wide else 0.55) * self.em)
            self._glyphs[char] = hit
        return hit

    def covers(self, char):
        return self._glyph(" " if char == NBSP else char)[0]

    def advance(self, text, shaping=SIMPLE, ligatures=True):
        """(advance in FontSize units, number of letter-spacing slots) of `text` as libass sets it."""
        if shaping == SIMPLE:
            # The simple shaper maps every code point to its nominal glyph: no kerning, no ligatures.
            total, count = 0.0, 0
            for char in text:
                if char in _INVISIBLE:
                    continue
                total += self._glyph(" " if char == NBSP else char)[1]
                count += 1
            return total, count
        key = (text, ligatures)
        hit = self._shaped.get(key)
        if hit is None:
            buffer = hb.Buffer()
            buffer.add_str(text)
            buffer.guess_segment_properties()
            # libass switches ligatures off as soon as a run has letter spacing.
            features = {"kern": True} if ligatures else {"kern": True, "liga": False, "clig": False}
            hb.shape(self.hb_font, buffer, features)
            total = sum(position.x_advance for position in buffer.glyph_positions)
            clusters = len({info.cluster for info in buffer.glyph_infos})
            hit = (total / self.height_units, clusters)
            if len(self._shaped) < 200000:
                self._shaped[key] = hit
        return hit


def _win_metrics(face):
    """usWinAscent/usWinDescent, the pair libass sizes a face by (hhea when both are zero)."""
    os2 = face.reference_table("OS/2").data
    if len(os2) >= 78:
        ascent, descent = struct.unpack(">HH", os2[74:78])
        if ascent + descent > 0:
            return ascent, descent
    hhea = face.reference_table("hhea").data
    if len(hhea) >= 8:
        ascent, descent = struct.unpack(">hh", hhea[4:8])
        if ascent - descent > 0:
            return ascent, -descent
    return face.upem * 0.8, face.upem * 0.2


_FACES = {}


def face_for(family):
    """The loaded face for a family name, or None when its file is not shipped."""
    if family not in _FACES:
        filename = FONT_FILES.get(family)
        path = os.path.join(FONTS_DIR, filename) if filename else None
        _FACES[family] = FontFace(family, path) if path and os.path.isfile(path) else None
    return _FACES[family]


def reset_fonts(fonts_dir=None):
    """Point the typesetter at another fonts directory (tests and the lab)."""
    global FONTS_DIR
    if fonts_dir:
        FONTS_DIR = str(fonts_dir)
    _FACES.clear()


def style_for(role, key):
    """The style of a script class in a role, or None when no shipped face is meant for it."""
    table, fallback = STYLES[role], STYLE_FALLBACK[role]
    seen = set()
    while key not in table and key in fallback and key not in seen:
        seen.add(key)
        key = fallback[key]
    return table.get(key)


# -------------------------------------------------------------- scripts ----

_SCRIPT_RANGES = [
    (0x0041, 0x005A, "latin"), (0x0061, 0x007A, "latin"), (0x00AA, 0x00AA, "latin"),
    (0x00BA, 0x00BA, "latin"), (0x00C0, 0x00D6, "latin"), (0x00D8, 0x00F6, "latin"),
    (0x00F8, 0x02AF, "latin"), (0x0370, 0x03FF, "greek"), (0x0400, 0x052F, "cyrillic"),
    (0x0531, 0x058F, "armenian"), (0x0590, 0x05FF, "hebrew"), (0x0600, 0x06FF, "arabic"),
    (0x0700, 0x074F, "syriac"), (0x0750, 0x077F, "arabic"), (0x0780, 0x07BF, "thaana"),
    (0x08A0, 0x08FF, "arabic"), (0x0900, 0x097F, "devanagari"), (0x0980, 0x09FF, "bengali"),
    (0x0A00, 0x0A7F, "gurmukhi"), (0x0A80, 0x0AFF, "gujarati"), (0x0B00, 0x0B7F, "oriya"),
    (0x0B80, 0x0BFF, "tamil"), (0x0C00, 0x0C7F, "telugu"), (0x0C80, 0x0CFF, "kannada"),
    (0x0D00, 0x0D7F, "malayalam"), (0x0D80, 0x0DFF, "sinhala"), (0x0E00, 0x0E7F, "thai"),
    (0x0E80, 0x0EFF, "lao"), (0x0F00, 0x0FFF, "tibetan"), (0x1000, 0x109F, "myanmar"),
    (0x10A0, 0x10FF, "georgian"), (0x1100, 0x11FF, "ko"), (0x1200, 0x139F, "ethiopic"),
    (0x1780, 0x17FF, "khmer"), (0x1C80, 0x1C8F, "cyrillic"), (0x1E00, 0x1EFF, "latin"),
    (0x1F00, 0x1FFF, "greek"), (0x2C60, 0x2C7F, "latin"), (0x2DE0, 0x2DFF, "cyrillic"),
    (0x2E80, 0x2FDF, "zh"), (0x3005, 0x3007, "zh"), (0x3021, 0x3029, "zh"),
    (0x3041, 0x3096, "ja"), (0x309D, 0x309F, "ja"), (0x30A1, 0x30FA, "ja"),
    (0x30FD, 0x30FF, "ja"), (0x3105, 0x312F, "zh"), (0x3131, 0x318E, "ko"),
    (0x31F0, 0x31FF, "ja"), (0x3400, 0x4DBF, "zh"), (0x4E00, 0x9FFF, "zh"),
    (0xA640, 0xA69F, "cyrillic"), (0xA720, 0xA7FF, "latin"), (0xA960, 0xA97F, "ko"),
    (0xAA60, 0xAA7F, "myanmar"), (0xAB30, 0xAB6F, "latin"), (0xAC00, 0xD7FF, "ko"),
    (0xF900, 0xFAFF, "zh"), (0xFB00, 0xFB06, "latin"), (0xFB1D, 0xFB4F, "hebrew"),
    (0xFB50, 0xFDFF, "arabic"), (0xFE70, 0xFEFC, "arabic"), (0xFF21, 0xFF3A, "latin"),
    (0xFF41, 0xFF5A, "latin"), (0xFF66, 0xFF9D, "ja"), (0xFFA0, 0xFFDC, "ko"),
    (0x1B000, 0x1B16F, "ja"), (0x20000, 0x323AF, "zh"),
]
_SCRIPT_STARTS = [start for start, _, _ in _SCRIPT_RANGES]

RTL_CLASSES = {"arabic", "hebrew", "syriac", "thaana"}
CJK_CLASSES = {"zh", "ja"}
# Written without spaces between words: breaks come from a phrase model or cluster rules.
SPACELESS_CLASSES = {"zh", "ja", "thai", "lao", "khmer", "myanmar", "tibetan"}
ALPHABETIC_CLASSES = {"latin", "cyrillic", "greek", "armenian", "georgian"}
# Need HarfBuzz: joining, reordering, conjuncts or mark positioning.
COMPLEX_CLASSES = RTL_CLASSES | {
    "devanagari", "bengali", "gurmukhi", "gujarati", "oriya", "tamil", "telugu", "kannada",
    "malayalam", "sinhala", "thai", "lao", "khmer", "myanmar", "tibetan",
}


def script_class(char):
    """Script class of a letter, '' for digits, punctuation, spaces and symbols."""
    code = ord(char)
    index = bisect.bisect_right(_SCRIPT_STARTS, code) - 1
    if index >= 0:
        start, end, name = _SCRIPT_RANGES[index]
        if start <= code <= end:
            return name
    return ""


def classify(texts):
    """Dominant script class of a whole track.

    Japanese is told from Chinese by its kana and Korean by Hangul, so the
    worker does not have to pass language codes.
    """
    counts = {}
    for text in texts:
        for char in text:
            name = script_class(char)
            if name:
                counts[name] = counts.get(name, 0) + 1
    if not counts:
        return "latin"
    han, kana = counts.pop("zh", 0), counts.pop("ja", 0)
    if han + kana:
        # An ideograph carries about as much as two or three letters.
        name = "ja" if kana >= max(2, 0.03 * (han + kana)) else "zh"
        counts[name] = 2 * (han + kana)
    if "ko" in counts:
        counts["ko"] *= 2
    for name in ("arabic", "hebrew"):
        if name in counts:
            counts[name] *= 1.5  # written without most vowels: fewer letters per word
    return max(counts, key=lambda name: (counts[name], name))


# Characters written in everyday Cantonese and hardly ever in Mandarin.
_CANTONESE = frozenset("嘅咗喺嚟哋啲嗰冇唔佢睇乜嘢噉咁")


def chinese_variant(texts):
    """'zh' (Simplified), 'zh-hant' (Traditional) or 'yue' (written Cantonese)."""
    simplified = traditional = cantonese = han = 0
    for text in texts:
        for char in text:
            if "一" <= char <= "鿿":
                han += 1
                in_gb, in_big5 = _encodes(char, "gb2312"), _encodes(char, "big5hkscs")
                simplified += in_gb and not in_big5
                traditional += in_big5 and not in_gb
                cantonese += char in _CANTONESE
    if traditional <= simplified:
        return "zh"
    if cantonese >= 3 and cantonese >= 0.02 * han:
        return "yue"
    return "zh-hant"


def _encodes(char, codec):
    try:
        char.encode(codec)
        return True
    except UnicodeEncodeError:
        return False


# ------------------------------------------------------------------ SRT ----

@dataclass
class Cue:
    start: int  # milliseconds
    end: int
    text: str


NBSP = " "
# Code points libass drops before rendering.
_INVISIBLE = frozenset(
    [chr(code) for code in range(0x200B, 0x2010)]
    + [chr(code) for code in range(0x202A, 0x202F)]
    + [chr(code) for code in range(0x2060, 0x2064)]
    + ["﻿", "­", "͏"]
)

_TIMING = re.compile(
    r"(\d+):(\d{1,2}):(\d{1,2})[,.](\d{1,3})\s*-->\s*(\d+):(\d{1,2}):(\d{1,2})[,.](\d{1,3})"
)
_MARKUP = re.compile(r"</?(?:i|b|u|s|font|c|v|ruby|rt)(?:\s[^>]*)?>", re.IGNORECASE)
_OVERRIDE = re.compile(r"\{[^{}]*\}")
_SPACES = re.compile("[ \t\r\n -  -  　]+")
_HARD_SPACES = re.compile("[   ]")


def clean_text(raw):
    """Plain text of one cue: no markup, no forced breaks, single spaces."""
    text = _MARKUP.sub("", raw)
    text = _OVERRIDE.sub("", text)
    text = text.replace("\\N", " ").replace("\\n", " ").replace("\\h", " ")
    text = text.replace("{", "(").replace("}", ")")
    text = "".join(
        char for char in text
        if char in "\n\t" or (unicodedata.category(char) != "Cc" and char not in "︎️")
    )
    text = unicodedata.normalize("NFC", text)
    # A no-break space keeps its meaning (French "mot !", "10 000") unless the
    # text is full of them, which is an export artefact and not typography.
    hard = len(_HARD_SPACES.findall(text))
    text = _HARD_SPACES.sub(NBSP if hard <= 4 else " ", text)
    text = _SPACES.sub(" ", text).strip()
    return text.strip(NBSP + " ")


def _milliseconds(hours, minutes, seconds, fraction):
    return (int(hours) * 3600 + int(minutes) * 60 + int(seconds)) * 1000 + int(fraction.ljust(3, "0"))


def parse_srt(data):
    """Cues of an SRT document, ordered by start, without empty or overlapping cues."""
    lines = data.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    cues = []
    index = 0
    while index < len(lines):
        match = _TIMING.search(lines[index])
        index += 1
        if not match:
            continue
        body = []
        while index < len(lines) and lines[index].strip():
            if _TIMING.search(lines[index]):
                # A cue with no blank line before it: drop the counter we just swallowed.
                if body and body[-1].strip().isdigit():
                    body.pop()
                break
            body.append(lines[index])
            index += 1
        groups = match.groups()
        start = _milliseconds(*groups[:4])
        end = _milliseconds(*groups[4:])
        text = clean_text("\n".join(body))
        if text and end > start:
            cues.append(Cue(start, end, text))
    cues.sort(key=lambda cue: (cue.start, cue.end))
    for current, following in zip(cues, cues[1:]):
        if current.end > following.start > current.start:
            current.end = following.start
    return cues


def read_srt(path):
    with open(path, "rb") as handle:
        return parse_srt(handle.read().decode("utf-8-sig", errors="replace"))


# ------------------------------------------------------------- geometry ----

@dataclass(frozen=True)
class Geometry:
    width: int
    height: int
    unit: float          # px per golden unit
    max_width: float     # widest line in px
    bottom: float        # px between the frame bottom and the secondary block
    centre: float


# The old script had 10-unit side margins on a 384-unit-wide grid.
SIDE_MARGIN = 10 / 384
BOTTOM_MARGIN = 20  # golden units
# Portrait video is read on a phone held upright: the frame is narrow, so type
# is sized from the width, and the block sits higher to clear the player's
# controls and caption area.
PORTRAIT_UNIT = 1.0
PORTRAIT_SIDE_MARGIN = 0.045
PORTRAIT_BOTTOM = 0.085  # share of the frame height
# Measured widths are a hair off what libass draws (fractional advances).
WIDTH_SAFETY = 0.995


def geometry(width, height):
    if height > width * 1.05:
        unit = width / 288 * PORTRAIT_UNIT
        side = PORTRAIT_SIDE_MARGIN * width
        bottom = PORTRAIT_BOTTOM * height
    else:
        unit = height / 288
        side = SIDE_MARGIN * width
        bottom = BOTTOM_MARGIN * unit
    return Geometry(width, height, unit, width - 2 * side, bottom, width / 2)


# --------------------------------------------------------------- tokens ----

@dataclass
class Run:
    face: FontFace
    style: Style
    text: str


@dataclass
class Token:
    """A piece of text that is never broken, and what breaking before it costs."""
    text: str
    space_before: bool = False
    penalty: float = 1.0     # cost of starting a line here; inf forbids it
    runs: list = field(default_factory=list)
    glyphs: float = 0.0      # width of the glyphs, golden units
    spacing: float = 0.0     # width added by letter spacing
    gap_glyphs: float = 0.0  # the space before it, when it stays on the line
    gap_spacing: float = 0.0
    ascent: float = 0.0
    descent: float = 0.0


INF = float("inf")

_NO_LINE_START = frozenset(
    "、。，．・：；？！゛゜ヽヾゝゞ々ー）〕］｝〉》」』】〙〗〟’”｠»‼⁇⁈⁉…‥～〜"
    "ぁぃぅぇぉっゃゅょゎゕゖァィゥェォッャュョヮヵヶㇰㇱㇲㇳㇴㇵㇶㇷㇸㇹㇺㇻㇼㇽㇾㇿ"
    ",.:;?!)]}%‰℃°"
)
_NO_LINE_END = frozenset("（〔［｛〈《「『【〘〖〝‘“｟«([{$¥￥£＄#＃@＠・")
_CLAUSE_END = frozenset(",;:.!?…，。、；：！？،؛؟।॥")
_SENTENCE_END = frozenset(".!?…。！？؟।॥")
_CJK_CLAUSE_END = frozenset("，、。；：！？")
_DASHES = frozenset("—–―-‐‒")
_CLOSERS = "\"'’”»)]}）」』】》〉"
_OPENERS = frozenset("\"'‘“„«([{（「『【《〈¿¡")
# Words that end in a full stop without ending a sentence.
_ABBREVIATIONS = frozenset(
    "mr mrs ms dr prof st jr sr vs mt inc ltd co nr ca bzw mme mlle sra dra sig approx".split()
)

# Dependent signs that must stay with the consonant before them, and leading
# vowels and stackers that must stay with the consonant after them.
_ATTACH_TO_PREVIOUS = [
    (0x0E30, 0x0E3A), (0x0E45, 0x0E4E), (0x0EB0, 0x0EBC), (0x0EC6, 0x0ECD),
    (0x102B, 0x103E), (0x1056, 0x1059), (0x17B6, 0x17D3),
]
_ATTACH_TO_NEXT = [(0x0E40, 0x0E44), (0x0EC0, 0x0EC4), (0x1039, 0x1039), (0x17D2, 0x17D2)]
_TSHEG = "་"  # Tibetan syllable mark: the only place a Tibetan line may break


def _in_ranges(char, ranges):
    code = ord(char)
    return any(start <= code <= end for start, end in ranges)


def _is_ideograph(char):
    """Han, kana and CJK punctuation: a line may break between any two of them."""
    if script_class(char) in CJK_CLASSES:
        return True
    code = ord(char)
    return 0x3000 <= code <= 0x303F or 0xFF00 <= code <= 0xFF65 or code in (0x30FB, 0x30FC)


def _is_katakana(char):
    return 0x30A1 <= ord(char) <= 0x30FA or char in "ーヽヾ"


def _is_spaceless(char):
    return script_class(char) in SPACELESS_CLASSES and not _is_ideograph(char)


def _is_native(char):
    return _is_ideograph(char) or _is_spaceless(char)


def _clusters(text):
    """Split into user-perceived characters: a base plus its marks and joiners."""
    out = []
    for char in text:
        category = unicodedata.category(char)
        joins = (
            category.startswith("M")
            or char in "‍‌︎️"
            or (out and out[-1][-1] == "‍")
        )
        if out and joins:
            out[-1] += char
        else:
            out.append(char)
    return out


_PARSERS = {}


def _phrase_parser(kind):
    """BudouX phrase model, or None when the package or the model is missing."""
    if kind not in _PARSERS:
        try:
            import budoux

            _PARSERS[kind] = {
                "ja": budoux.load_default_japanese_parser,
                "zh-hans": budoux.load_default_simplified_chinese_parser,
                "zh-hant": budoux.load_default_traditional_chinese_parser,
                "thai": budoux.load_default_thai_parser,
            }[kind]()
        except Exception:
            _PARSERS[kind] = None
    return _PARSERS[kind]


@functools.lru_cache(maxsize=20000)
def _phrase_starts(text, kind):
    """Offsets in `text` where a new phrase starts by the phrase model, or None without a model."""
    parser = _phrase_parser(kind) if kind else None
    if parser is None:
        return None
    starts, offset = set(), 0
    try:
        for phrase in parser.parse(text):
            if offset:
                starts.add(offset)
            offset += len(phrase)
    except Exception:
        return None
    return frozenset(starts)


# The Chinese phrase model sometimes sets a one-character word apart, and a line
# then starts with a particle or ends on a preposition. A particle or a suffix
# belongs to what comes before it, a preposition or an adverb to what follows,
# and a measure word to its number.
_HAN_TRAILING = frozenset("的地得了着著过過吗嗎呢吧啊呀嘛们們器机機性化者员員嘅咗緊喇啦㗎咩囉哋")
_HAN_LEADING = frozenset(
    "在从從到和与與跟同把被对對向给給比为為由于於以及或但而且就也都还還又再不没沒很更最是将將让讓使若如因当當却卻才只既喺唔冇"
)
_HAN_NUMERALS = frozenset("0123456789〇一二三四五六七八九十百千万萬亿億两兩几幾数數多半")
_HAN_MEASURES = frozenset("个個台部位只隻条條张張件种種次年月日天岁歲元块塊倍辆輛秒")


# The model was trained on written Chinese and does not know the Cantonese among
# these words. Applied to all Traditional Chinese: a short film in Cantonese may
# not be recognised as such, and the others start a clause in Mandarin as well.
_YUE_CONNECTIVES = ("同埋", "但係", "不過", "因為", "所以", "如果", "或者", "仲有", "即係", "而家")


def _chinese_phrase_starts(text, starts, cantonese=False):
    """`starts` without the seams that would strand a one-character function word."""
    kept = set(starts)
    if cantonese:
        for word in _YUE_CONNECTIVES:
            at = text.find(word)
            while at != -1:
                if at:
                    kept.add(at)
                kept.difference_update(range(at + 1, at + len(word)))
                at = text.find(word, at + len(word))
    starts = frozenset(kept)
    for offset in sorted(starts):
        char = text[offset]
        alone = offset + 1 >= len(text) or offset + 1 in starts
        if char in _HAN_MEASURES and text[offset - 1] in _HAN_NUMERALS:
            kept.discard(offset)  # 数十亿 | 台
        elif alone and char in _HAN_TRAILING:
            kept.discard(offset)  # 各种各样 | 的, 伺服 | 器
    for offset in sorted(kept | {0}):
        if offset + 1 in kept and text[offset] in _HAN_LEADING:
            kept.discard(offset + 1)  # 由 | 网页浏览器
    return frozenset(kept)


PENALTY_CLAUSE = 0.3         # after CJK clause punctuation
PENALTY_PHRASE = 1.0         # between two phrases of a spaceless script
PENALTY_INSIDE_PHRASE = 4.0  # inside a phrase: legal, but only when nothing else fits
PENALTY_SCRIPT_SEAM = 2.0    # between a Latin word or number and an ideograph
PENALTY_NO_MODEL = 8.0       # between clusters of a spaceless script we have no model for
PENALTY_HYPHEN = 3.0
PENALTY_NAME = 3.0           # between two foreign words inside CJK text, between two numbers


def _may_break_between(previous, following):
    last, first = previous[-1], following[0]
    if first in _NO_LINE_START or last in _NO_LINE_END:
        return False
    if last == first and last in "—…‥─":
        return False
    if _in_ranges(first, _ATTACH_TO_PREVIOUS) or _in_ranges(last, _ATTACH_TO_NEXT):
        return False
    if _is_katakana(last) and _is_katakana(first):
        return False  # a loanword is one word
    if last.isdigit() and (_is_ideograph(first) or first.isdigit()):
        return False  # a number and its counter: 1995年, 10日間, 3个
    if last == "第" and first.isdigit():
        return False
    return True


def _split_chunk(chunk, track):
    """Pieces of one space-free chunk as (text, penalty of breaking before it)."""
    clusters = _clusters(chunk)
    kinds = [
        "ideo" if _is_ideograph(c[0]) else "spaceless" if _is_spaceless(c[0]) else "word"
        for c in clusters
    ]
    if "ideo" not in kinds and "spaceless" not in kinds:
        return _split_hyphens(chunk)

    entries = []  # (text, penalty)
    index = 0
    while index < len(clusters):
        kind = kinds[index]
        end = index
        while end < len(clusters) and kinds[end] == kind:
            end += 1
        group = clusters[index:end]
        if kind == "word":
            entries.append(("".join(group), PENALTY_SCRIPT_SEAM))
            index = end
            continue
        text = "".join(group)
        if kind == "ideo":
            starts = _phrase_starts(text, track.phrase_kind)
            if starts is not None and track.phrase_kind in ("zh-hans", "zh-hant"):
                starts = _chinese_phrase_starts(text, starts, cantonese=track.phrase_kind == "zh-hant")
            inside = PENALTY_INSIDE_PHRASE if starts is not None else PENALTY_SCRIPT_SEAM
        else:
            script = script_class(group[0][0])
            starts = _phrase_starts(text, "thai") if script == "thai" else None
            inside = INF if starts is not None else PENALTY_NO_MODEL
        offset = 0
        for position, cluster in enumerate(group):
            if position == 0:
                penalty = PENALTY_SCRIPT_SEAM
            elif starts is not None and offset in starts:
                penalty = PENALTY_PHRASE
            else:
                penalty = inside
            if position and group[position - 1][-1] in _CJK_CLAUSE_END:
                penalty = PENALTY_CLAUSE
            if position and kind == "spaceless" and script_class(cluster[0]) == "tibetan":
                penalty = PENALTY_PHRASE if group[position - 1][-1] == _TSHEG else INF
            entries.append((cluster, penalty))
            offset += len(cluster)
        index = end

    # Forbidden breaks, then glue everything that may not be separated into one piece.
    pieces = []
    for position, (text, penalty) in enumerate(entries):
        if position and not _may_break_between(entries[position - 1][0], text):
            penalty = INF
        if pieces and penalty == INF:
            pieces[-1][0] += text
        else:
            pieces.append([text, penalty])
    return [(text, penalty) for text, penalty in pieces]


def _split_hyphens(chunk):
    """A long hyphenated compound may break after a hyphen; everything else stays whole."""
    if len(chunk) < 12 or "-" not in chunk[4:-4]:
        return [(chunk, 1.0)]
    pieces, start = [], 0
    for position, char in enumerate(chunk):
        if char == "-" and position - start >= 3 and len(chunk) - position > 4:
            if chunk[position + 1].isalpha() and chunk[position - 1].isalpha():
                pieces.append((chunk[start:position + 1], PENALTY_HYPHEN))
                start = position + 1
    pieces.append((chunk[start:], PENALTY_HYPHEN))
    return pieces


def _is_abbreviation(word):
    """`word` ends in a full stop that most likely does not end a sentence."""
    stem = word[:-1].lstrip("\"'‘“„«([{")
    if not stem:
        return False
    if "." in stem:
        return True  # U.S., e.g., z.B.
    if stem.isdigit():
        return len(stem) <= 2  # German ordinals: am 3. Mai (a year ends a sentence)
    return (len(stem) == 1 and stem.isalpha()) or stem.lower() in _ABBREVIATIONS


def _space_penalty(tokens, following, cls):
    """Cost of breaking at the space between the last token and `following`."""
    previous = tokens[-1].text
    last, first = previous[-1], following[0]
    core = previous.rstrip(_CLOSERS)

    if not any(char.isalnum() for char in following):
        # A lone mark. A dash stays on the line before it ("устройств —"), unless
        # it opens a new speaker's sentence; French "? ! : ; »" stay as well.
        if first in _DASHES:
            return 0.0 if core and core[-1] in _SENTENCE_END else INF
        return 0.6 if first in _OPENERS else INF
    if not any(char.isalnum() for char in previous):
        if last in _DASHES:
            # After a dash is a fine place to break, unless the dash opens the line.
            return 0.0 if tokens[-1].penalty == INF else INF
        if last in _OPENERS and last not in "\"'":
            return INF
        return 1.0

    if last.isdigit() and _is_ideograph(first):
        return INF  # number and counter, written with a space: 1995 年
    if last.isdigit() and first.isdigit():
        return PENALTY_NAME  # 10 000
    if core and core[-1] in _CLAUSE_END:
        if core[-1] == "." and _is_abbreviation(core):
            return 2.5
        return 0.0

    if cls in SPACELESS_CLASSES:
        native_before, native_after = _is_native(last), _is_native(first)
        if native_before and native_after:
            return 0.0  # the pipeline writes clause punctuation as a space
        if native_before != native_after:
            return PENALTY_SCRIPT_SEAM
        return PENALTY_NAME  # inside a run of foreign words, most often a name

    penalty = 1.0
    if cls in ALPHABETIC_CLASSES:
        letters = [char for char in previous if char.isalpha()]
        year = previous.isdigit() and len(previous) == 4 and previous[0] in "12"
        if letters and len(letters) <= 3 and len(previous) == len(letters):
            penalty += 1.5  # article, preposition or conjunction left hanging at the line end
        elif previous.isdigit() and first.islower() and not year:
            penalty += 0.7  # a number and what it counts: "10 | days"
        elif first.isdigit():
            penalty += 0.7  # a number and what introduces it: "more than | 200"
        if previous[0].isupper() and first.isupper() and len(letters) > 1:
            penalty += 0.8  # probably a name
        if following.islower() and following.isalpha() and len(following) <= 3 and (len(letters) > 3 or year):
            penalty -= 0.3  # a new line may well start with a function word
    if first in _OPENERS:
        penalty -= 0.4
    return penalty


def tokenize(text, track):
    tokens = []
    for chunk in text.split(" "):
        if not chunk:
            continue
        for piece_index, (piece, penalty) in enumerate(_split_chunk(chunk, track)):
            token = Token(piece, penalty=penalty)
            if not tokens:
                token.penalty = 0.0
            elif piece_index == 0:
                token.space_before = True
                token.penalty = _space_penalty(tokens, piece, track.cls)
            tokens.append(token)
    return tokens


# ------------------------------------------------------- fonts per track ----

@dataclass
class Track:
    role: str
    cls: str                      # dominant script class: how the text is tokenised
    key: str                      # style key: cls, or the Chinese variant
    style: Style
    face: FontFace
    phrase_kind: str = None       # BudouX model for its ideographs
    rtl: bool = False
    word_fallback: Style = None   # for whole words the face has no letters for
    latin: Style = None           # Latin words and digits are set in this instead
    latin_fallback: Style = None


# A secondary Latin track keeps the golden face only while that face can set
# its letters. A stray foreign name moves one word to the companion face; a
# language the face cannot write moves the whole track (two faces mixed word
# by word throughout a film look like a ransom note).
COMPANION_SHARE = 0.003  # share of letters outside the golden face that moves the track


def plan_track(role, texts):
    cls = classify(texts)
    key = chinese_variant(texts) if cls == "zh" else cls
    style = style_for(role, key) or STYLES[role]["latin"]
    track = Track(role, cls, key, style, None)

    golden = STYLES[SECONDARY]["latin"]
    companion = STYLES[SECONDARY]["latin+"]
    if role == SECONDARY and face_for(companion.family) is not None:
        golden_face = face_for(golden.family)
        if cls in _LONG_TAIL:
            track.latin, track.latin_fallback = golden, companion
        elif style == golden:
            letters = [
                char for text in texts for char in text if script_class(char) in ALPHABETIC_CLASSES
            ]
            missing = sum(1 for char in letters if golden_face is None or not golden_face.covers(char))
            if golden_face is None or missing > COMPANION_SHARE * len(letters):
                track.style = companion
            else:
                track.word_fallback = companion
    elif role == MAIN and cls in _LONG_TAIL:
        track.latin = STYLES[MAIN]["latin"]

    track.face = face_for(track.style.family)
    if track.face is None:
        raise RuntimeError(f"subtitle font is missing: {track.style.family}")
    track.phrase_kind = {"ja": "ja", "zh": "zh-hans", "zh-hant": "zh-hant", "yue": "zh-hant"}.get(key)
    track.rtl = cls in RTL_CLASSES
    return track


def track_family(role, texts):
    """The family a track of these texts is set in (before any fallback for missing letters)."""
    cls = classify(texts)
    key = chinese_variant(texts) if cls == "zh" else cls
    return (style_for(role, key) or STYLES[role]["latin"]).family


def _lacks_letters(face, text):
    return any(script_class(char) in ALPHABETIC_CLASSES and not face.covers(char) for char in text)


def _foreign_style(track, char):
    """Face and style for a character the track's own face cannot set."""
    cls = script_class(char)
    keys = list(HAN_KEYS) if cls in CJK_CLASSES else [cls] if cls else []
    seen = set()
    for key in keys + FALLBACK_KEYS:
        style = style_for(track.role, key)
        if style is None or style.family in seen:
            continue
        seen.add(style.family)
        face = face_for(style.family)
        if face is not None and face.covers(char):
            return face, style
    for family in FONT_FILES:
        face = face_for(family)
        if face is not None and family not in seen and face.covers(char):
            # Same em as the track's face, so a stray symbol does not look pasted in.
            size = track.style.size * track.face.em / face.em
            return face, Style(family, round(size, 2))
    return track.face, track.style


def assign_runs(token, track):
    """Decide which face sets each character of a token."""
    base_face, base_style = track.face, track.style
    if track.word_fallback is not None and _lacks_letters(base_face, token.text):
        base_style = track.word_fallback
        base_face = face_for(base_style.family)
    latin_face = latin_style = None
    if track.latin is not None:
        latin_style = track.latin
        latin_face = face_for(latin_style.family)
        if latin_face is None or (track.latin_fallback and _lacks_letters(latin_face, token.text)):
            latin_style = track.latin_fallback or latin_style
            latin_face = face_for(latin_style.family)

    runs = []
    for cluster in _clusters(token.text):
        char = cluster[0]
        cls = script_class(char)
        digit = "0" <= char <= "9"
        previous = runs[-1] if runs else None
        if char in _INVISIBLE or char == NBSP:
            face, style = (previous.face, previous.style) if previous else (base_face, base_style)
        elif latin_face is not None and (cls == "latin" or digit) and latin_face.covers(char):
            face, style = latin_face, latin_style
        elif not cls and not digit and previous is not None and previous.face.covers(char):
            face, style = previous.face, previous.style  # punctuation follows its word
        elif base_face.covers(char):
            face, style = base_face, base_style
        else:
            face, style = _foreign_style(track, char)
        if previous is not None and previous.face is face and previous.style == style:
            previous.text += cluster
        else:
            runs.append(Run(face, style, cluster))
    token.runs = runs


def measure(token, shaping, previous=None):
    """Fill in a token's widths and vertical extent from its runs."""
    token.glyphs = token.spacing = token.ascent = token.descent = 0.0
    for run in token.runs:
        style = run.style
        advance, slots = run.face.advance(run.text, shaping, ligatures=not style.spacing)
        token.glyphs += advance * style.size * style.scale_x
        token.spacing += slots * style.spacing * style.scale_x
        token.ascent = max(token.ascent, run.face.ascent * style.size)
        token.descent = max(token.descent, run.face.descent * style.size)
    token.gap_glyphs = token.gap_spacing = 0.0
    if token.space_before and previous is not None and previous.runs:
        run = previous.runs[-1]
        advance, _ = run.face.advance(" ", SIMPLE)
        token.gap_glyphs = advance * run.style.size * run.style.scale_x
        token.gap_spacing = run.style.spacing * run.style.scale_x


# -------------------------------------------------------- line breaking ----

RAGGED_WEIGHT = 6.0    # against break penalties of about 1 per ordinary word space
PYRAMID_WEIGHT = 0.6   # a shorter first line reads better and hides less picture
# A line that is a little too long is tightened before it is broken: first the
# letter spacing (nobody sees that), then the glyphs are narrowed by a few
# percent. The font size never changes, so the two tracks keep their relation.
SPACING_STEPS = (0.75, 0.5, 0.25, 0.0)
MIN_SCALE_X = {MAIN: 0.94, SECONDARY: 0.90}
# Once a cue needs a second line anyway, tightening only pays when it buys a
# better break: these are its costs on the scale of the break penalties.
SPACING_STEP_COST = 0.08
SCALE_PERCENT_COST = 0.4
EXTRA_LINES = 2          # how many lines over the minimum are considered
EXTRA_LINE_COST = 2.0    # what one more line costs, against a better break or less tightening


class _Widths:
    """Line widths of a token list at one tightening level."""

    def __init__(self, tokens, spacing_factor, scale):
        self.words = [0.0]
        self.gaps = [0.0]
        for token in tokens:
            self.words.append(self.words[-1] + scale * (token.glyphs + spacing_factor * token.spacing))
            self.gaps.append(self.gaps[-1] + scale * (token.gap_glyphs + spacing_factor * token.gap_spacing))

    def line(self, start, end):
        return self.words[end] - self.words[start] + self.gaps[end] - self.gaps[start + 1]


def _atoms(tokens):
    """Index ranges of tokens that may not be separated."""
    ranges, start = [], 0
    for index in range(1, len(tokens)):
        if tokens[index].penalty != INF:
            ranges.append((start, index))
            start = index
    ranges.append((start, len(tokens)))
    return ranges


def _min_lines(tokens, widths, limit):
    """Fewest lines that hold every token under `limit`, or None when something is too wide."""
    best = [INF] * (len(tokens) + 1)
    best[0] = 0
    for end in range(1, len(tokens) + 1):
        for start in range(end - 1, -1, -1):
            if widths.line(start, end) > limit:
                break
            if best[start] != INF and (start == 0 or tokens[start].penalty != INF):
                best[end] = min(best[end], best[start] + 1)
    return None if best[-1] == INF else best[-1]


def _balanced(tokens, widths, limit, count):
    """Break into exactly `count` lines: balanced, at the best seams, never over `limit`."""
    total = len(tokens)
    target = widths.line(0, total) / count
    cost = [[INF] * (total + 1) for _ in range(count + 1)]
    back = [[0] * (total + 1) for _ in range(count + 1)]
    cost[0][0] = 0.0
    for line in range(1, count + 1):
        for end in range(line, total + 1):
            for start in range(end - 1, line - 2, -1):
                width = widths.line(start, end)
                if width > limit:
                    break
                previous = cost[line - 1][start]
                if previous == INF:
                    continue
                penalty = tokens[start].penalty if start else 0.0
                if penalty == INF:
                    continue
                value = previous + penalty + RAGGED_WEIGHT * ((width - target) / limit) ** 2
                if line == 1 and count == 2:
                    # Two lines: a slightly shorter first line wins a near tie.
                    value += PYRAMID_WEIGHT * max(0.0, 2 * width - 2 * target) / limit
                if value < cost[line][end]:
                    cost[line][end] = value
                    back[line][end] = start
    if cost[count][total] == INF:
        return None, INF
    bounds, end = [], total
    for line in range(count, 0, -1):
        start = back[line][end]
        bounds.append((start, end))
        end = start
    bounds.reverse()
    return bounds, cost[count][total]


def _levels(tokens, limit, role):
    """Tightening levels to try, loosest first, as (spacing factor, horizontal scale, cost)."""
    levels = [(1.0, 1.0, 0.0)]
    factor, cost = 1.0, 0.0
    if any(token.spacing or token.gap_spacing for token in tokens):
        for factor in SPACING_STEPS:
            cost += SPACING_STEP_COST
            levels.append((factor, 1.0, cost))
    percent = 99
    while percent >= round(MIN_SCALE_X[role] * 100):
        cost += SCALE_PERCENT_COST
        levels.append((factor, percent / 100, cost))
        percent -= 1
    # Something that cannot be broken is wider than the frame even at the
    # tightest level (a URL, a very long compound): narrow the whole cue to fit.
    factor, scale, cost = levels[-1]
    widths = _Widths(tokens, factor, scale)
    widest = max(widths.line(start, end) for start, end in _atoms(tokens))
    if widest > limit:
        levels = [(factor, scale * limit / widest * 0.999, cost)]
    return levels


def _best_break(tokens, limit, levels, count):
    """Cheapest way to set the cue in `count` lines: (cost, bounds, (spacing factor, scale))."""
    best = None
    for factor, scale, level_cost in levels:
        if best is not None and level_cost >= best[0]:
            break
        widths = _Widths(tokens, factor, scale)
        needed = _min_lines(tokens, widths, limit)
        if needed is None or needed > count:
            continue
        bounds, cost = _balanced(tokens, widths, limit, count)
        if bounds is None:
            continue
        if count == 1:
            return 0.0, bounds, (factor, scale)
        if best is None or cost + level_cost < best[0]:
            best = (cost + level_cost, bounds, (factor, scale))
    return best


def fit(tokens, limit, role):
    """Line breaks and tightening for one cue: (list of token lists, (spacing factor, scale)).

    One long line is better than two: a cue that fits one line, at the loosest
    setting that holds it, is never broken. A cue that has to be broken is
    tightened only as far as that buys a better place to break, and it takes one
    line more than the minimum when the minimum can only be had by cutting
    through a word or a phrase (narrow frames: portrait and square video).
    """
    if not tokens:
        return [], (1.0, 1.0)
    levels = _levels(tokens, limit, role)
    chosen, first = None, None
    for count in range(1, len(tokens) + 1):
        if first is not None and count > first + EXTRA_LINES:
            break
        best = _best_break(tokens, limit, levels, count)
        if best is None:
            continue
        if count == 1:
            return [tokens], best[2]
        if first is None:
            first = count
        total = best[0] + EXTRA_LINE_COST * (count - first)
        if chosen is None or total < chosen[0]:
            chosen = (total, best[1], best[2])
    if chosen is not None:
        return [tokens[start:end] for start, end in chosen[1]], chosen[2]
    factor, scale, _ = levels[-1]
    return [tokens], (factor, scale)


# ----------------------------------------------------------------- ASS ----

YELLOW = "&H0000FFFF"
WHITE = "&H00FFFFFF"
BLACK = "&H00000000"
BOX = "&H40000000"
OUTLINE = 1.0  # golden units
RLM = "‏"


@dataclass(frozen=True)
class Look:
    """What the user may change about a track: colours, outline and a size factor.

    `scale` multiplies every size of the track (font, letter spacing, the room
    it takes); `outline` is in golden units and does not follow `scale`, as
    `Outline` does not follow `FontSize` in an ASS style.
    """
    colour: str
    outline_colour: str = BLACK
    back_colour: str = BOX
    outline: float = OUTLINE
    scale: float = 1.0


LOOKS = {MAIN: Look(YELLOW), SECONDARY: Look(WHITE)}


@dataclass
class Block:
    """One typeset cue."""
    start: int
    end: int
    lines: list
    squeeze: tuple     # (spacing factor, horizontal scale)
    height: float      # golden units
    shaping: str


@dataclass
class Script:
    """One ASS document and the libass shaper it has to be rendered with."""
    name: str
    shaping: str
    text: str


def typeset_cue(cue, track, geom):
    shaping = COMPLEX if any(script_class(char) in COMPLEX_CLASSES for char in cue.text) else SIMPLE
    tokens = tokenize(cue.text, track)
    previous = None
    for token in tokens:
        assign_runs(token, track)
        measure(token, shaping, previous)
        previous = token
    lines, squeeze = fit(tokens, geom.max_width / geom.unit * WIDTH_SAFETY, track.role)
    height = sum(
        max(token.ascent for token in line) + max(token.descent for token in line) for line in lines
    )
    return Block(cue.start, cue.end, lines, squeeze, height, shaping)


def _number(value, digits=3):
    text = f"{value:.{digits}f}"
    return text.rstrip("0").rstrip(".") if "." in text else text


def _run_state(style, unit, squeeze):
    factor, scale = squeeze
    return (
        style.family,
        _number(style.size * unit),
        _number(style.spacing * factor * unit),
        _number(style.scale_x * scale * 100, 2),
    )


_STATE_TAGS = ("\\fn", "\\fs", "\\fsp", "\\fscx")


def _event_text(block, track, geom, bottom_y):
    state = _run_state(track.style, geom.unit, (1.0, 1.0))
    parts = ["{\\an2\\pos(%s,%s)}" % (_number(geom.centre, 2), _number(bottom_y, 2))]
    for line_index, line in enumerate(block.lines):
        if line_index:
            parts.append("\\N")
        if track.rtl and any(script_class(c) in RTL_CLASSES for token in line for c in token.text):
            parts.append(RLM)  # base direction of the line; libass decides it per line
        for token_index, token in enumerate(line):
            if token_index and token.space_before:
                parts.append(" ")
            for run in token.runs:
                wanted = _run_state(run.style, geom.unit, block.squeeze)
                if wanted != state:
                    parts.append("{%s}" % "".join(
                        tag + value for tag, value, old in zip(_STATE_TAGS, wanted, state) if value != old
                    ))
                    state = wanted
                parts.append(run.text)
    return "".join(parts)


def _timestamp(milliseconds):
    centiseconds = (milliseconds + 5) // 10
    hours, rest = divmod(centiseconds, 360000)
    minutes, rest = divmod(rest, 6000)
    seconds, centiseconds = divmod(rest, 100)
    return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"


def _document(track, geom, shaping, events, look):
    unit = geom.unit  # already scaled by look.scale
    style = track.style
    boxed = track.role == MAIN
    colour = look.colour
    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {geom.width}",
        f"PlayResY: {geom.height}",
        "WrapStyle: 2",
        "ScaledBorderAndShadow: yes",
    ]
    if shaping == COMPLEX:
        lines.append("Kerning: yes")
    lines += [
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
        "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Default,{style.family},{_number(style.size * unit)},{colour},{colour},"
        f"{look.outline_colour},{look.back_colour},"
        f"0,0,0,0,{_number(style.scale_x * 100, 2)},100,{_number(style.spacing * unit)},0,"
        f"{4 if boxed else 1},{_number(look.outline * unit / look.scale)},0,2,0,0,0,{-1 if track.rtl else 1}",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    return "\n".join(lines + events) + "\n"


# A secondary cue this much taller than one plain line pushes the translation up.
SLOT_TOLERANCE = 1.12


def _slot_heights(main_blocks, secondary_blocks, nominal):
    """Height reserved under every main cue: the tallest secondary cue it shares the screen with.

    A one-line secondary always reserves its nominal line, so the translation
    does not hop from cue to cue.
    """
    heights = []
    first = 0
    for block in main_blocks:
        while first < len(secondary_blocks) and secondary_blocks[first].end <= block.start:
            first += 1
        height = nominal
        index = first
        while index < len(secondary_blocks) and secondary_blocks[index].start < block.end:
            other = secondary_blocks[index]
            overlap = min(block.end, other.end) - max(block.start, other.start)
            shortest = min(block.end - block.start, other.end - other.start)
            if overlap >= min(100, shortest / 2) and other.height > nominal * SLOT_TOLERANCE:
                height = max(height, other.height)
            index += 1
        heights.append(height)
    return heights


def build_scripts(source_cues, translated_cues, width, height, looks=None):
    """ASS scripts for a source (secondary) and a translated (main) cue list.

    `looks` maps MAIN and SECONDARY to a `Look`; LOOKS by default. Returns
    (scripts, summary). The scripts are to be rendered in order, each with its
    own shaper; `filter_chain` writes the ffmpeg filters for them.
    """
    looks = {**LOOKS, **(looks or {})}
    geom = geometry(width, height)
    # Every size of a track is in units of its own geometry: the golden unit times its scale.
    role_geom = {role: replace(geom, unit=geom.unit * looks[role].scale) for role in (MAIN, SECONDARY)}
    summary = {"width": width, "height": height}
    secondary_y = height - geom.bottom
    scripts = []

    secondary = secondary_blocks = None
    nominal = STYLES[SECONDARY]["latin"].size
    if source_cues:
        sgeom = role_geom[SECONDARY]
        secondary = plan_track(SECONDARY, [cue.text for cue in source_cues])
        secondary_blocks = [typeset_cue(cue, secondary, sgeom) for cue in source_cues]
        nominal = secondary.style.size
        positions = [secondary_y] * len(secondary_blocks)
        scripts += _scripts(secondary, sgeom, secondary_blocks, positions, looks[SECONDARY])
        summary[SECONDARY] = _describe(secondary, secondary_blocks)
    if translated_cues:
        mgeom = role_geom[MAIN]
        main = plan_track(MAIN, [cue.text for cue in translated_cues])
        main_blocks = [typeset_cue(cue, main, mgeom) for cue in translated_cues]
        # The translation sits on the room the original takes, or would take: the
        # same place whether the original is burnt in or not.
        slots = _slot_heights(main_blocks, secondary_blocks or [], nominal)
        positions = [secondary_y - slot * role_geom[SECONDARY].unit for slot in slots]
        scripts += _scripts(main, mgeom, main_blocks, positions, looks[MAIN])
        summary[MAIN] = _describe(main, main_blocks)
    return scripts, summary


def _scripts(track, geom, blocks, positions, look):
    scripts = []
    for shaping in (SIMPLE, COMPLEX):
        events = [
            f"Dialogue: 0,{_timestamp(block.start)},{_timestamp(block.end)},Default,,0,0,0,,"
            + _event_text(block, track, geom, y)
            for block, y in zip(blocks, positions)
            if block.shaping == shaping and block.lines
        ]
        if events:
            suffix = "" if shaping == SIMPLE else "_complex"
            text = _document(track, geom, shaping, events, look)
            scripts.append(Script(f"{track.role}{suffix}.ass", shaping, text))
    return scripts


def _describe(track, blocks):
    return {
        "script": track.key,
        "font": track.style.family,
        "size": track.style.size,
        "cues": len(blocks),
        "two_lines": sum(1 for block in blocks if len(block.lines) == 2),
        "more_lines": sum(1 for block in blocks if len(block.lines) > 2),
        "tightened": sum(1 for block in blocks if block.squeeze != (1.0, 1.0)),
    }


_PLAIN_PATH = re.compile(r"[\w./+-]+")


def filter_chain(scripts, fonts_dir="fonts", directory=""):
    """The ffmpeg filters that burn `scripts`, in order.

    `directory` is where `typeset_files` wrote them; without it the names are
    relative to ffmpeg's working directory.
    """
    filters = []
    for script in scripts:
        path = f"{directory.rstrip('/')}/{script.name}" if directory else script.name
        for value in (path, fonts_dir):
            if not _PLAIN_PATH.fullmatch(value):
                raise ValueError(f"path needs escaping in an ffmpeg filter: {value!r}")
        filters.append(f"ass={path}:fontsdir={fonts_dir}:shaping={script.shaping}")
    return ",".join(filters)


def typeset_files(source_srt, translated_srt, out_dir, width, height, looks=None):
    """Write the ASS scripts for two SRT files into `out_dir`. Returns (scripts, summary)."""
    source_cues = read_srt(source_srt) if source_srt else []
    translated_cues = read_srt(translated_srt) if translated_srt else []
    scripts, summary = build_scripts(source_cues, translated_cues, width, height, looks)
    for script in scripts:
        with open(os.path.join(out_dir, script.name), "w", encoding="utf-8") as handle:
            handle.write(script.text)
    return scripts, summary


if __name__ == "__main__":
    if len(sys.argv) != 6:
        sys.exit("usage: typeset.py source.srt translated.srt width height out_dir")
    written, info = typeset_files(sys.argv[1], sys.argv[2], sys.argv[5], int(sys.argv[3]), int(sys.argv[4]))
    print(info)
    print(filter_chain(written))
