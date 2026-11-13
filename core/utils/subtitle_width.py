"""How wide subtitle text is drawn, and the line breaks the plain `subtitles` filter can not make.

Widths are in units of 1/80 of a landscape subtitle row: a Latin letter is about 1 on both
rows, so `subtitle.max_length: 80` is one full row. core/_5_split_sub.py splits the lines by
them. Nothing here needs the typesetting libraries, so the plain filter can use it as well.
"""
import bisect
import math
import re
import unicodedata

# How wide one character is drawn, measured with the fonts and sizes core/utils/typeset.py sets
# each script in: (first, last, on the translation row, on the source row).
CJK_WIDTHS = [
    (0x1100, 0x11FF, 2.57, 2.11),  # Hangul jamo
    (0x3000, 0x303F, 2.84, 2.27),  # CJK punctuation
    (0x3040, 0x30FF, 2.79, 2.27),  # Kana
    (0x3130, 0x318F, 2.57, 2.11),  # Hangul compatibility jamo
    (0x3400, 0x4DBF, 2.84, 2.27),  # Han, extension A
    (0x4E00, 0x9FFF, 2.84, 2.27),  # Han
    (0xAC00, 0xD7A3, 2.57, 2.11),  # Hangul
    (0xF900, 0xFAFF, 2.84, 2.27),  # Han, compatibility forms
    (0xFF01, 0xFF60, 2.84, 2.27),  # Full-width forms
]
OTHER_WIDTHS = [
    (0x0400, 0x052F, 1.14, 1.13),  # Cyrillic
    (0x0590, 0x05FF, 1.24, 1.13),  # Hebrew
    (0x0600, 0x06FF, 1.31, 1.21),  # Arabic
    (0x0900, 0x097F, 1.15, 1.05),  # Devanagari
    (0x0980, 0x09FF, 1.28, 1.18),  # Bengali
    (0x0A00, 0x0A7F, 1.00, 0.91),  # Gurmukhi
    (0x0A80, 0x0AFF, 1.07, 0.97),  # Gujarati
    (0x0B00, 0x0B7F, 1.29, 1.19),  # Oriya
    (0x0B80, 0x0BFF, 1.60, 1.47),  # Tamil
    (0x0C00, 0x0C7F, 1.04, 0.95),  # Telugu
    (0x0C80, 0x0CFF, 1.26, 1.16),  # Kannada
    (0x0D00, 0x0D7F, 1.53, 1.41),  # Malayalam
    (0x0D80, 0x0DFF, 1.36, 1.25),  # Sinhala
    (0x0E00, 0x0E7F, 1.13, 1.05),  # Thai
    (0x0E80, 0x0EFF, 1.07, 1.00),  # Lao
    (0x1000, 0x109F, 1.19, 1.10),  # Myanmar
    (0x1780, 0x17FF, 1.10, 1.02),  # Khmer
]
CHAR_WIDTHS = sorted(CJK_WIDTHS + OTHER_WIDTHS)
_FIRST_CODES = [first for first, _, _, _ in CHAR_WIDTHS]
# Subtitles in a CJK font: its Latin letters and digits are wide, its spaces and half-width punctuation narrow
CJK_FONT_ALNUM = (1.5, 1.2)
CJK_FONT_OTHER = (0.85, 0.7)
TRANSLATION, SOURCE = 0, 1  # the row a line is shown on


def char_width(char, row, cjk_font):
    code = ord(char)
    i = bisect.bisect_right(_FIRST_CODES, code) - 1
    if i >= 0 and code <= CHAR_WIDTHS[i][1]:
        return CHAR_WIDTHS[i][2 + row]
    if cjk_font:
        return (CJK_FONT_ALNUM if char.isalnum() else CJK_FONT_OTHER)[row]
    return 1


def line_width(text, row, cjk_font):
    """Width of one subtitle line shown on `row`, in units of 1/80 of a landscape row."""
    return sum(char_width(char, row, cjk_font) for char in str(text))


def uses_cjk_font(lines):
    """Whether the subtitles set these lines in a Chinese, Japanese or Korean font.

    The typesetter picks one font for the whole track, with the same rule: an ideograph
    or a Hangul syllable carries about as much as two letters.
    """
    cjk = other = 0
    for line in lines:
        for char in str(line):
            if char.isalpha():
                if any(first <= ord(char) <= last for first, last, _, _ in CJK_WIDTHS):
                    cjk += 1
                else:
                    other += 1
    return 2 * cjk > other


# ------------
# Lines for the plain subtitles filter
# ------------

# The plain filter (libass, `WrapStyle` 0) breaks a line at its spaces only, so a Chinese,
# Japanese or Thai line wider than the frame runs off both sides. Its default fonts (Arial
# Unicode MS, Noto Sans CJK) draw about 88 units of `line_width(..., SOURCE, True)` on one
# row of a 16:9 frame at the translation size 17; 80 leaves room for other fonts. Latin
# letters are drawn about as wide as in a CJK font, hence `cjk_font=True` for every line.
PLAIN_ROW = 80
PLAIN_FONT_SIZE = 17
# Scripts written without spaces between words: Thai, Lao, Myanmar, Khmer, kana and Han
UNSPACED = [(0x0E00, 0x0EFF), (0x1000, 0x109F), (0x1780, 0x17FF), (0x3040, 0x30FF),
            (0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF)]
FULL_WIDTH = [(0x3000, 0x303F), (0xFF01, 0xFF60)]
SOUTHEAST_ASIAN = [(0x0E00, 0x0EFF), (0x1000, 0x109F), (0x1780, 0x17FF)]
# A row never starts with these: closing marks, small kana, iteration and prolonged sound marks
CLOSING = set("、。，．,.!?！？;；:：)）]］}｝」』】〉》〕〗〙〛’”%％…‥ー々〻ゝゞヽヾ"
              "ぁぃぅぇぉっゃゅょゎゕゖァィゥェォッャュョヮヵヶ")
# ... nor ends with these
OPENING = set("([{（［｛「『【〈《〔〖〘〚‘“")
# A row may end after a pause at no cost
PAUSES = set("、。，．！？；：…")
# Thai and Lao vowels written before their consonant, and those that only follow one
LEADING_VOWELS = set("เแโใไເແໂໃໄ")
FOLLOWING_VOWELS = set("ะาำๅๆະາຳໆ")
# Cost of a break inside a phrase of Chinese or Japanese, and inside a word of the other scripts
PHRASE_BREAK, CJK_BREAK, OTHER_BREAK = 0.02, 0.08, 0.5

_PARSERS = {}


def _within(ranges, char):
    code = ord(char)
    return any(first <= code <= last for first, last in ranges)


def _phrase_parser(kind):
    """The BudouX model for `kind`, None without BudouX."""
    if kind not in _PARSERS:
        try:
            import budoux

            _PARSERS[kind] = {
                "ja": budoux.load_default_japanese_parser,
                "zh-hans": budoux.load_default_simplified_chinese_parser,
                "thai": budoux.load_default_thai_parser,
            }[kind]()
        except Exception:
            _PARSERS[kind] = None
    return _PARSERS[kind]


def _phrase_starts(text):
    """The indexes of `text` where BudouX starts a phrase; none without BudouX."""
    if any(_within([(0x3040, 0x30FF)], char) for char in text):
        kind = "ja"
    elif any(_within([(0x0E00, 0x0E7F)], char) for char in text):
        kind = "thai"
    elif any(_within(UNSPACED[4:], char) for char in text):
        kind = "zh-hans"
    else:
        return set()
    parser = _phrase_parser(kind)
    if parser is None:
        return set()
    starts, position = set(), 0
    for phrase in parser.parse(text)[:-1]:
        position += len(phrase)
        starts.add(position)
    return starts


def _break_costs(text):
    """The cost of starting a row at each index of `text`, None where a row must not start."""
    phrases = _phrase_starts(text)
    costs = [None] * len(text)
    for i in range(1, len(text)):
        before, after = text[i - 1], text[i]
        if before == " " or after == " ":
            costs[i] = 0.0
        elif (after in CLOSING or after in FOLLOWING_VOWELS or unicodedata.category(after)[0] == "M"
              or before in OPENING or before in LEADING_VOWELS or unicodedata.combining(before) == 9):
            continue  # 9: a virama or coeng joins the next consonant to its own
        elif before in PAUSES:
            costs[i] = 0.0
        elif any(_within(UNSPACED + FULL_WIDTH, char) for char in (before, after)):
            if i in phrases:
                costs[i] = PHRASE_BREAK
            elif any(_within(SOUTHEAST_ASIAN, char) for char in (before, after)):
                costs[i] = OTHER_BREAK
            else:
                costs[i] = CJK_BREAK
        # Anything else is inside a word of a script written with spaces
    return costs


def _balanced_rows(text, prefix, costs, rows, capacity):
    """(cost, rows of `text`) for the best `rows` rows, or None when they can not be made."""
    points = [0] + [i for i, cost in enumerate(costs) if cost is not None] + [len(text)]
    target = prefix[-1] / rows

    def width(start, end):  # of text[start:end] without the spaces at its ends
        while start < end and text[start] == " ":
            start += 1
        while end > start and text[end - 1] == " ":
            end -= 1
        return prefix[end] - prefix[start]

    last = len(points) - 1
    best = [[math.inf] * len(points) for _ in range(rows + 1)]
    back = [[0] * len(points) for _ in range(rows + 1)]
    best[0][0] = 0.0
    for count in range(1, rows + 1):
        for j in ([last] if count == rows else range(1, last)):
            extra = 0.0 if j == last else costs[points[j]]
            for i in range(j - 1, -1, -1):
                drawn = width(points[i], points[j])
                if drawn > 1.5 * capacity:
                    break  # only gets wider
                if best[count - 1][i] == math.inf or drawn == 0:
                    continue
                cost = ((drawn - target) / capacity) ** 2 + extra
                if drawn > capacity:
                    cost += 1 + 10 * (drawn - capacity) / capacity
                if best[count - 1][i] + cost < best[count][j]:
                    best[count][j], back[count][j] = best[count - 1][i] + cost, i
    if best[rows][last] == math.inf:
        return None
    parts, j = [], last
    for count in range(rows, 0, -1):
        i = back[count][j]
        parts.append(text[points[i]:points[j]].strip())
        j = i
    return best[rows][last], parts[::-1]


def plain_row_capacity(width, height, font_size):
    """How much of `line_width(..., SOURCE, True)` one row of the plain filter holds.

    The filter draws its letters in proportion to the frame height, so a row holds less
    on a portrait frame, and less at a larger font size.
    """
    return PLAIN_ROW * (width / height) / (16 / 9) * PLAIN_FONT_SIZE / max(font_size, 1)


def wrap_line(text, capacity):
    """`text` broken into balanced rows of at most `capacity` when the plain filter could not do it.

    Only lines with Chinese, Japanese, Thai, Lao, Khmer or Burmese in them are broken here: the
    filter breaks the others at their spaces itself. Rows end at spaces and after commas and
    full stops where they can, else between BudouX phrases, else between two characters.
    """
    if not any(_within(UNSPACED, char) for char in text):
        return text
    stripped = text.strip()
    widths = [char_width(char, SOURCE, True) for char in stripped]
    prefix = [0.0]
    for value in widths:
        prefix.append(prefix[-1] + value)
    if prefix[-1] <= capacity:
        return text
    costs = _break_costs(stripped)
    rows = math.ceil(prefix[-1] / capacity)
    best = _balanced_rows(stripped, prefix, costs, rows, capacity)
    if best is None or best[0] >= 1:  # a row is too wide: try one more
        more = _balanced_rows(stripped, prefix, costs, rows + 1, capacity)
        if more is not None and (best is None or more[0] < best[0]):
            best = more
    return "\n".join(best[1]) if best else text


def wrap_srt(content, capacity):
    """SRT `content` with its lines broken by `wrap_line`, None when none had to be."""
    blocks = re.split(r"\n[ \t]*\n", content.replace("\r\n", "\n").strip("\n"))
    changed = False
    for index, block in enumerate(blocks):
        lines = block.split("\n")
        timing = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if timing is None:
            continue
        for i in range(timing + 1, len(lines)):
            wrapped = wrap_line(lines[i], capacity)
            if wrapped != lines[i]:
                lines[i], changed = wrapped, True
        blocks[index] = "\n".join(lines)
    return "\n\n".join(blocks) + "\n" if changed else None
