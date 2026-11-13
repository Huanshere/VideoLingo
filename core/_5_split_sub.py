import bisect
import re

import pandas as pd
from typing import List, Tuple
import concurrent.futures

from core._1_ytdlp import find_subtitle_file
from core._3_2_split_meaning import split_sentence
from core.task_runner import StopTask
from core.prompts import get_align_prompt
from rich.panel import Panel
from rich.console import Console
from rich.table import Table
from core.utils import *
from core.utils.config_utils import get_text_joiner
from core.utils.models import *
console = Console()

# How wide one character is drawn in the burned-in subtitles, in units of 1/80 of a landscape
# subtitle row: a Latin letter is about 1 on both rows, so `subtitle.max_length: 80` is one
# full row. Measured with the fonts and sizes core/utils/typeset.py sets each script in:
# (first, last, on the translation row, on the source row).
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

# The source row is small and stays on one row. The translation row is the one people read:
# it is set larger and reads well as two balanced rows, so a translation may be this many
# rows wide before its line is split (about 46 Chinese characters or 130 Latin letters).
# Splitting earlier means more lines cut in two by the model, and looser source/translation pairs.
TRANSLATION_ROWS = 1.65

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

def length_check(src_lines, tr_lines):
    """A function telling whether one (source, translation) line is too long for the subtitles."""
    subtitle_set = load_key("subtitle")
    max_length, multiplier = subtitle_set["max_length"], subtitle_set["target_multiplier"]
    src_cjk, tr_cjk = uses_cjk_font(src_lines), uses_cjk_font(tr_lines)

    def too_long(src, tr):
        tr = re.sub(r'[，。]', ' ', str(tr)).strip()  # shown without them, see `align_timestamp`
        return line_width(src, SOURCE, src_cjk) > max_length or \
               line_width(tr, TRANSLATION, tr_cjk) / TRANSLATION_ROWS * multiplier > max_length

    return too_long

def get_target_parts(response_data, num_parts):
    """The aligned target parts of a response, or None unless there are exactly `num_parts` non-empty ones."""
    align_data = response_data.get('align') if isinstance(response_data, dict) else None
    if not isinstance(align_data, list) or len(align_data) != num_parts:
        return None
    parts = []
    for i, item in enumerate(align_data):
        part = item.get(f'target_part_{i+1}') if isinstance(item, dict) else None
        if not isinstance(part, str) or not part.strip():
            return None
        parts.append(part.strip())
    return parts

def align_subs(src_sub: str, tr_sub: str, src_part: str) -> Tuple[List[str], List[str], str]:
    align_prompt = get_align_prompt(src_sub, tr_sub, src_part)
    src_parts = src_part.split('\n')
    
    def valid_align(response_data):
        if 'align' not in response_data:
            return {"status": "error", "message": "Missing required key: `align`"}
        if get_target_parts(response_data, len(src_parts)) is None:
            return {"status": "error", "message": f"Align does not contain {len(src_parts)} non-empty parts as expected!"}
        return {"status": "success", "message": "Align completed"}
    parsed = ask_gpt(align_prompt, resp_type='json', valid_def=valid_align, log_title='align_subs')
    tr_parts = get_target_parts(parsed, len(src_parts))
    
    # The parts are in the target language, so the source-language joiner does not apply
    tr_remerged = join_words(tr_parts, get_text_joiner(''.join(tr_parts)))
    
    table = Table(title="🔗 Aligned parts")
    table.add_column("Language", style="cyan")
    table.add_column("Parts", style="magenta")
    table.add_row("SRC_LANG", "\n".join(src_parts))
    table.add_row("TARGET_LANG", "\n".join(tr_parts))
    console.print(table)
    
    return src_parts, tr_parts, tr_remerged

def split_align_subs(src_lines: List[str], tr_lines: List[str]):
    too_long = length_check(src_lines, tr_lines)
    remerged_tr_lines = tr_lines.copy()
    
    to_split = []
    for i, (src, tr) in enumerate(zip(src_lines, tr_lines)):
        src, tr = str(src), str(tr)
        if too_long(src, tr):
            to_split.append(i)
            table = Table(title=f"📏 Line {i} needs to be split")
            table.add_column("Type", style="cyan")
            table.add_column("Content", style="magenta")
            table.add_row("Source Line", src)
            table.add_row("Target Line", tr)
            console.print(table)
    
    @except_handler("Error in split_align_subs")
    def process(i):
        split_src = split_sentence(src_lines[i], num_parts=2).strip()
        if len([part for part in split_src.split('\n') if part.strip()]) < 2:
            console.print(f"[yellow]⚠️ Line {i} could not be split, keeping it as is[/yellow]")
            return
        src_parts, tr_parts, tr_remerged = align_subs(src_lines[i], tr_lines[i], split_src)
        # Source and translation must stay in step: a line is split on both sides or not at all
        if not tr_parts or len(src_parts) != len(tr_parts):
            console.print(f"[yellow]⚠️ Line {i} was aligned into a different number of parts, keeping it as is[/yellow]")
            return
        src_lines[i] = src_parts
        tr_lines[i] = tr_parts
        remerged_tr_lines[i] = tr_remerged
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=load_key("max_workers")) as executor:
        futures = [executor.submit(process, i) for i in to_split]
    for i, future in zip(to_split, futures):
        error = future.exception()
        if isinstance(error, StopTask):
            raise error
        if error:
            console.print(f"[yellow]⚠️ Line {i} is kept unsplit: {error}[/yellow]")
    
    # Flatten `src_lines` and `tr_lines`
    src_lines = [item for sublist in src_lines for item in (sublist if isinstance(sublist, list) else [sublist])]
    tr_lines = [item for sublist in tr_lines for item in (sublist if isinstance(sublist, list) else [sublist])]
    
    return src_lines, tr_lines, remerged_tr_lines

def split_source_lines(lines: List[str]) -> List[str]:
    """Split the lines that are too long for a subtitle, for subtitles without a translation."""
    max_length = load_key("subtitle")["max_length"]
    cjk_font = uses_cjk_font(lines)

    def fits(line):
        return line_width(line, SOURCE, cjk_font) <= max_length

    def process(line):
        if fits(line):
            return [line]
        parts = [part.strip() for part in split_sentence(line, num_parts=2).split('\n') if part.strip()]
        return parts if len(parts) > 1 else [line]

    for _ in range(3):
        if all(fits(line) for line in lines):
            break
        check_cancel()
        with concurrent.futures.ThreadPoolExecutor(max_workers=load_key("max_workers")) as executor:
            lines = [part for parts in executor.map(process, lines) for part in parts]
    return lines

def split_for_sub_main():
    console.print("[bold green]🚀 Start splitting subtitles...[/bold green]")
    
    df = pd.read_excel(_4_2_TRANSLATION)
    src = df['Source'].tolist()
    trans = df['Translation'].tolist()

    if find_subtitle_file():
        # The subtitles of the user keep their lines and their times
        console.print("[cyan]📄 Subtitles of the user: the lines are kept as they are[/cyan]")
        for path in (_5_SPLIT_SUB, _5_REMERGED):
            pd.DataFrame({'Source': src, 'Translation': trans}).to_excel(path, index=False)
        return
    
    for attempt in range(3):  # 多次切割
        console.print(Panel(f"🔄 Split attempt {attempt + 1}", expand=False))
        split_src, split_trans, remerged = split_align_subs(src.copy(), trans)
        
        # 检查是否所有字幕都符合长度要求
        too_long = length_check(split_src, split_trans)
        if not any(too_long(src_line, tr_line) for src_line, tr_line in zip(split_src, split_trans)):
            break
        
        # 更新源数据继续下一轮分割
        src, trans = split_src, split_trans

    # 确保二者有相同的长度，防止报错
    if len(src) > len(remerged):
        remerged += [None] * (len(src) - len(remerged))
    elif len(remerged) > len(src):
        src += [None] * (len(remerged) - len(src))
    
    pd.DataFrame({'Source': split_src, 'Translation': split_trans}).to_excel(_5_SPLIT_SUB, index=False)
    pd.DataFrame({'Source': src, 'Translation': remerged}).to_excel(_5_REMERGED, index=False)

if __name__ == '__main__':
    split_for_sub_main()
