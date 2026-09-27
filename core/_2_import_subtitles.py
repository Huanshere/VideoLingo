"""Subtitles of the user take the place of the recognition and of the sentence splitting."""
import os
import re

import pandas as pd

from core._1_ytdlp import find_media_file, find_subtitle_file, sanitize_filename, write_input_manifest
from core.utils import load_key, rprint
from core.utils.models import _2_CLEANED_CHUNKS, _3_1_SPLIT_BY_NLP, _3_2_SPLIT_BY_MEANING

# Inside output/, as the generated subtitles are in output/ itself
SUBTITLE_DIR = "input"
CUE_TIMES = re.compile(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)")
TAGS = re.compile(r"<[^>]*>|\{\\[^}]*\}")  # <i> <font color=...> {\an8}


def read_cues(content: bytes):
    """The subtitles of an SRT file as (start, end, text) in seconds, one line of text for each."""
    try:
        text = content.decode("utf-16" if content.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig")
    except UnicodeDecodeError:
        raise ValueError("The subtitles are not saved as UTF-8. Save them as UTF-8 and retry.")

    blocks = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        times = CUE_TIMES.search(line)
        if times:
            if blocks and lines[i - 1].strip().isdigit():
                blocks[-1][2].pop()  # the number of this subtitle
            h1, m1, s1, ms1, h2, m2, s2, ms2 = times.groups()
            start = int(h1) * 3600 + int(m1) * 60 + float(f"{s1}.{ms1}")
            end = int(h2) * 3600 + int(m2) * 60 + float(f"{s2}.{ms2}")
            blocks.append((start, end, []))
        elif blocks:
            blocks[-1][2].append(line)

    cues = []
    for start, end, lines in sorted(blocks, key=lambda block: block[0]):
        text = " ".join(TAGS.sub("", " ".join(lines)).split())
        # Without a letter or a digit there is nothing to translate, such as "♪"
        if end > start and re.sub(r"[^\w\s]", "", text).strip():
            cues.append((start, end, text))
    if not cues:
        raise ValueError("No subtitles were found. The file has to be an SRT file with text.")
    return cues


def add_input_subtitles(name, content: bytes, save_path="output"):
    """Keep the subtitles with the input. Without a media file they are the input themselves."""
    read_cues(content)
    folder = os.path.join(save_path, SUBTITLE_DIR)
    os.makedirs(folder, exist_ok=True)
    subtitle_file = os.path.join(folder, sanitize_filename(os.path.splitext(name)[0]) + ".srt")
    with open(subtitle_file, "wb") as f:
        f.write(content)
    try:
        media_file, media_type = find_media_file(save_path)
    except ValueError as e:
        if "No media file found" not in str(e):
            raise
        media_file, media_type = subtitle_file, "subtitle"
    write_input_manifest(media_file, media_type, save_path, subtitle_file)
    return subtitle_file


def get_words(cues):
    """The words of the subtitles. The time of a subtitle is shared among its words by their length."""
    words = []
    for start, end, text in cues:
        parts = text.split()
        # Without the punctuation, as the lines are matched with the words without it: "-" takes no time
        lengths = [len(re.sub(r"[^\w\s]", "", part)) for part in parts]
        total = sum(lengths)
        done = 0
        for part, length in zip(parts, lengths):
            word_start = start + (end - start) * done / total
            done += length
            words.append({"text": f'"{part}"', "start": round(word_start, 3),
                          "end": round(start + (end - start) * done / total, 3), "speaker_id": None})
    return words


def import_subtitles():
    """Write the results of the recognition and of the sentence splitting from the subtitles of the user."""
    subtitle_file = find_subtitle_file()
    if not subtitle_file or os.path.exists(_2_CLEANED_CHUNKS):
        return
    if load_key("whisper.language") == "auto":
        raise ValueError("The language of subtitles can not be detected. "
                         "Select their language as the recognition language and retry.")
    with open(subtitle_file, "rb") as f:
        cues = read_cues(f.read())

    # The dubbing needs the audio of the video, as after a recognition
    media_file, media_type = find_media_file()
    if media_type == "video":
        from core._2_asr import prepare_audio
        prepare_audio(media_file, media_type, load_key("demucs"))

    os.makedirs(os.path.dirname(_2_CLEANED_CHUNKS), exist_ok=True)
    sentences = "\n".join(text for _, _, text in cues)
    for path in (_3_1_SPLIT_BY_NLP, _3_2_SPLIT_BY_MEANING):
        with open(path, "w", encoding="utf-8") as f:
            f.write(sentences)
    pd.DataFrame(get_words(cues)).to_excel(_2_CLEANED_CHUNKS, index=False)
    rprint(f"[green]📄 {len(cues)} subtitles of `{subtitle_file}` are used instead of the recognition.[/green]")
