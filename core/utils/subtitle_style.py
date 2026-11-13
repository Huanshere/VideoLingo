"""Style and languages of the burned-in subtitles, from `subtitle` in config.yaml.

Without a font name the subtitles are set by the built-in typesetter
(typeset.py): a font and a size per writing system, lines broken by their
rendered width, burnt with ffmpeg's `ass` filter. With a font name, or when the
typesetter can not be used, ffmpeg's `subtitles` filter sets them in that font
(the system's default font without one); the lines it can not break itself are
broken beforehand (subtitle_width.py).
"""
import os
import platform
import re
import shutil

from rich import print as rprint
from rich.markup import escape

from .config_utils import load_key_or, update_key

# An empty font name stands for the built-in typesetting (the default font of the system without it)
DEFAULT_STYLE = {
    "source": {
        "font_name": "", "font_size": 15, "font_color": "&HFFFFFF",
        "outline_color": "&H000000", "outline_width": 1,
    },
    "translation": {
        "font_name": "", "font_size": 17, "font_color": "&H00FFFF",
        "outline_color": "&H000000", "outline_width": 1,
        "back_color": "&H33000000", "margin_v": 27,
    },
}
COLOR_KEYS = {"font_color", "outline_color", "back_color"}

BURN_MODES = ("bilingual", "translation", "source")
# The key of each video in config.yaml and what it shows without the key
BURN_MODE_KEYS = {"subtitle": ("subtitle.sub_video_subtitles", "bilingual"), "dubbed": ("subtitle.dub_video_subtitles", "translation")}


def default_font():
    # Linux needs the Google Noto fonts: apt-get install fonts-noto
    return {"Linux": "NotoSansCJK-Regular", "Darwin": "Arial Unicode MS"}.get(platform.system(), "Arial")


def to_ass_color(value):
    """`&HBBGGRR`, `&HAABBGGRR` or `#RRGGBB` as an ASS colour, None when it is none of them."""
    value = str(value).strip()
    if re.fullmatch(r"&[Hh]([0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})", value):
        return "&H" + value[2:].upper()
    if re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
        return f"&H{value[5:7]}{value[3:5]}{value[1:3]}".upper()
    return None


def to_hex_color(ass_color):
    """The `#rrggbb` of an ASS colour, without its transparency."""
    return f"#{ass_color[-2:]}{ass_color[-4:-2]}{ass_color[-6:-4]}".lower()


def clean_value(key, value):
    """The value as it goes into the ffmpeg filter, None when it can not be used."""
    if key in COLOR_KEYS:
        return to_ass_color(value)
    if key == "font_name":
        # These characters would end the value inside the filter
        return None if not isinstance(value, str) or re.search(r"[,:;='\\\[\]]", value) else value.strip()
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        return None
    return value


def get_subtitle_style(kind):
    """The style of the `source` or `translation` subtitles; a missing or unusable value is the default one."""
    configured = load_key_or("subtitle.style", None)
    configured = configured.get(kind) if isinstance(configured, dict) else None
    configured = configured if isinstance(configured, dict) else {}
    style = {}
    for key, default in DEFAULT_STYLE[kind].items():
        value = clean_value(key, configured.get(key, default))
        if value is None:
            rprint(f"[yellow]⚠️ subtitle.style.{kind}.{key} = {configured[key]!r} can not be used, using {default!r}[/yellow]")
            value = default
        style[key] = value
    return style


def save_subtitle_style(style):
    """Write the changed values one by one, so that the comments of config.yaml are kept."""
    changes = [
        (kind, key) for kind in style for key, value in style[kind].items()
        if value != get_subtitle_style(kind).get(key)
    ]
    try:
        if all(update_key(f"subtitle.style.{kind}.{key}", style[kind][key], add_missing=True) for kind, key in changes):
            return
    except KeyError:
        pass
    # A config.yaml from before this setting, or one with a broken `style`
    update_key("subtitle.style", style, add_missing=True)


def get_force_style(kind):
    """The `force_style` of the subtitles filter of ffmpeg."""
    style = get_subtitle_style(kind)
    parts = [
        f"FontSize={style['font_size']}", f"FontName={style['font_name'] or default_font()}",
        f"PrimaryColour={style['font_color']}", f"OutlineColour={style['outline_color']}",
        f"Outline={style['outline_width']}",
    ]
    if kind == "translation":
        parts += [f"BackColour={style['back_color']}", "Alignment=2", f"MarginV={style['margin_v']}", "BorderStyle=4"]
    else:
        parts.append("BorderStyle=1")
    return ",".join(parts)


def get_burn_mode(video):
    """Which subtitles go into the `subtitle` or `dubbed` video: bilingual, translation or source."""
    key, default = BURN_MODE_KEYS[video]
    mode = load_key_or(key, default)
    if mode not in BURN_MODES:
        rprint(f"[yellow]⚠️ {key} = {mode!r} can not be used, using {default!r}[/yellow]")
        mode = default
    return mode


def get_shown_kinds(video, source_srt):
    """`source` and/or `translation`: the subtitles burnt into a video, the source ones first."""
    mode = get_burn_mode(video)
    if mode != "translation" and not os.path.exists(source_srt):
        # A dub from before the source subtitles of the dub were written
        rprint(f"[yellow]⚠️ {source_srt} not found, burning the translated subtitles only[/yellow]")
        mode = "translation"
    return ["source", "translation"] if mode == "bilingual" else [mode]


# Where the scripts of the typesetter and the SRT files of the plain filter are written, one folder per video
TYPESET_DIR = "output/ass"


def get_plain_srt(video, kind, srt_file, width, height):
    """`srt_file`, or a copy of it with the lines broken that the plain filter would draw off the frame.

    The filter breaks a line at its spaces only: a long Chinese, Japanese or Thai line has none.
    """
    try:
        from .subtitle_width import plain_row_capacity, wrap_srt

        with open(srt_file, encoding="utf-8-sig") as handle:
            content = handle.read()
        capacity = plain_row_capacity(width, height, get_subtitle_style(kind)["font_size"])
        wrapped = wrap_srt(content, capacity)
        if wrapped is None:
            return srt_file
        target = f"{TYPESET_DIR}/{video}/plain_{kind}.srt"
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(wrapped)
        return target
    except Exception as error:  # burn the file as it is rather than not at all
        rprint(f"[yellow]⚠️ Could not break the long lines of {escape(srt_file)} ({escape(str(error))}), burning it as it is[/yellow]")
        return srt_file


def get_subtitle_filters(video, source_srt, translation_srt, kinds=None, width=0, height=0):
    """The `subtitles` filters of ffmpeg for a video, the source subtitles below the translated ones.

    With the size of the frame, lines too wide for it are broken first (`get_plain_srt`).
    """
    kinds = kinds or get_shown_kinds(video, source_srt)
    subtitles = {"source": source_srt, "translation": translation_srt}
    if width > 0 and height > 0:
        subtitles = {kind: get_plain_srt(video, kind, subtitles[kind], width, height) for kind in kinds}
    return ",".join(f"subtitles={subtitles[kind]}:force_style='{get_force_style(kind)}'" for kind in kinds)


# The font size of DEFAULT_STYLE is the typesetter's own size; another one scales it, within these bounds
SCALE_RANGE = (0.25, 4.0)


def get_look(kind, style=None):
    """The `Look` of the typesetter for the `source` or `translation` subtitles."""
    from .typeset import BOX, Look

    style = style or get_subtitle_style(kind)
    scale = style["font_size"] / DEFAULT_STYLE[kind]["font_size"]
    return Look(
        colour=style["font_color"], outline_colour=style["outline_color"],
        back_colour=style.get("back_color", BOX), outline=style["outline_width"],
        scale=min(max(scale, SCALE_RANGE[0]), SCALE_RANGE[1]),
    )


def get_typeset_filters(video, source_srt, translation_srt, width, height, kinds=None):
    """The `ass` filters of the built-in typesetter for a video, None when it can not be used."""
    kinds = kinds or get_shown_kinds(video, source_srt)
    styles = {kind: get_subtitle_style(kind) for kind in kinds}
    if any(style["font_name"] for style in styles.values()):
        return None  # a font of the user's choice: the subtitles filter sets everything in it
    if width <= 0 or height <= 0:
        rprint(f"[yellow]⚠️ The video size could not be read ({width}x{height}), using the plain subtitles filter[/yellow]")
        return None
    try:
        from . import subtitle_fonts, typeset
    except ImportError as error:
        rprint(f"[yellow]⚠️ Built-in subtitle typesetting is not available ({escape(str(error))}), "
               "run the installer again to get it. Using the plain subtitles filter.[/yellow]")
        return None
    try:
        roles = {"source": typeset.SECONDARY, "translation": typeset.MAIN}
        srt_files = {"source": source_srt, "translation": translation_srt}
        cues = {kind: typeset.read_srt(srt_files[kind]) for kind in kinds}
        families = [typeset.track_family(roles[kind], [cue.text for cue in cues[kind]]) for kind in kinds if cues[kind]]
        if not subtitle_fonts.ensure(families):
            rprint("[yellow]⚠️ A subtitle font could not be downloaded, using the plain subtitles filter[/yellow]")
            return None
        looks = {roles[kind]: get_look(kind, styles[kind]) for kind in kinds}
        scripts, _ = typeset.build_scripts(
            cues.get("source", []), cues.get("translation", []), width, height, looks
        )
        if not scripts:
            return None
        out_dir = f"{TYPESET_DIR}/{video}"
        shutil.rmtree(out_dir, ignore_errors=True)  # scripts of an earlier run must not be burnt in
        os.makedirs(out_dir)
        for script in scripts:
            with open(os.path.join(out_dir, script.name), "w", encoding="utf-8") as handle:
                handle.write(script.text)
        # Relative paths: a Windows drive letter would need escaping inside the filter
        fonts_dir = os.path.relpath(typeset.FONTS_DIR).replace(os.sep, "/")
        return typeset.filter_chain(scripts, fonts_dir, out_dir)
    except Exception as error:  # never lose the video to the typesetter: burn it the plain way
        from core.task_runner import StopTask

        if isinstance(error, StopTask):  # the user stopped the task while a font was downloading
            raise
        rprint(f"[yellow]⚠️ Built-in subtitle typesetting failed ({escape(str(error))}), using the plain subtitles filter[/yellow]")
        return None


def get_subtitle_filter_candidates(video, source_srt, translation_srt, width, height):
    """The subtitle filters to try in turn: the typesetter's `ass` filters if they can be used, then the plain ones."""
    kinds = get_shown_kinds(video, source_srt)
    # The typesetter first: it empties the folder of the video that the plain filter writes to as well
    typeset_filters = get_typeset_filters(video, source_srt, translation_srt, width, height, kinds)
    plain_filters = get_subtitle_filters(video, source_srt, translation_srt, kinds, width, height)
    return [typeset_filters, plain_filters] if typeset_filters else [plain_filters]
