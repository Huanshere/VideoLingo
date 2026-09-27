"""Style of the burned-in subtitles, from `subtitle.style` in config.yaml."""
import platform
import re

from rich import print as rprint

from .config_utils import load_key_or, update_key

# An empty font name stands for the default font of the system
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
