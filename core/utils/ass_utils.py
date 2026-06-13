import os
import pandas as pd

ASS_OUTPUT_CONFIGS = [
    ('src.ass', ['Source']),
    ('trans.ass', ['Translation']),
    ('src_trans.ass', ['Source', 'Translation']),
    ('trans_src.ass', ['Translation', 'Source']),
]


def seconds_to_ass_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds * 100) % 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _srt_timestamp_to_seconds(ts_str):
    parts = ts_str.strip().split(' --> ')
    start_str, end_str = parts[0], parts[1]

    def parse(hmsm):
        h, m, s_ms = hmsm.split(':')
        s, ms = s_ms.split(',')
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0

    return parse(start_str), parse(end_str)


def _get_default_style(name):
    defaults = {
        'source': {
            'fontname': 'Arial', 'fontsize': 17,
            'primary_color': '&HFFFFFF', 'secondary_color': '&HFFFFFF',
            'outline_color': '&H000000', 'back_color': '&H000000',
            'bold': 0, 'italic': 0, 'border_style': 1,
            'outline_width': 1.0, 'shadow': 0.0, 'alignment': 8,
            'margin_l': 10, 'margin_r': 10, 'margin_v': 10,
            'shadow_color': '&H80000000',
        },
        'translation': {
            'fontname': 'Arial', 'fontsize': 17,
            'primary_color': '&H00FFFF', 'secondary_color': '&H00FFFF',
            'outline_color': '&H000000', 'back_color': '&H33000000',
            'bold': 0, 'italic': 0, 'border_style': 4,
            'outline_width': 1.0, 'shadow': 0.0, 'alignment': 2,
            'margin_l': 10, 'margin_r': 10, 'margin_v': 27,
        },
    }
    return defaults.get(name, defaults['translation'])


def _build_style_line(style_name, config):
    d = _get_default_style(style_name)
    merged = {**d, **config}
    outline = merged['outline_width']
    shadow = merged['shadow']
    if isinstance(outline, float) and outline == int(outline):
        outline = int(outline)
    if isinstance(shadow, float) and shadow == int(shadow):
        shadow = int(shadow)
    return (
        f"Style: {style_name.capitalize()},"
        f"{merged['fontname']},{merged['fontsize']},"
        f"{merged['primary_color']},{merged['secondary_color']},"
        f"{merged['outline_color']},{merged['back_color']},"
        f"{merged['bold']},{merged['italic']},0,0,"
        f"100,100,0,0,"
        f"{merged['border_style']},{outline},{shadow},"
        f"{merged['alignment']},"
        f"{merged['margin_l']},{merged['margin_r']},{merged['margin_v']},1"
    )


def parse_ass_style_line(line):
    line = line.strip()
    if line.lower().startswith('style:'):
        line = line[len('style:'):].strip()
    # Remove inline comments
    if '*' in line:
        line = line[:line.index('*')].strip()
    parts = [p.strip() for p in line.split(',')]
    if len(parts) < 22:
        raise ValueError(f"ASS Style line needs >=22 fields, got {len(parts)}")
    # Map: (0-based index in parts, config key, value_type)
    # parts[0] = Name (skipped)
    field_map = {
        1: ('fontname', str),
        2: ('fontsize', int),
        3: ('primary_color', str),
        4: ('secondary_color', str),
        5: ('outline_color', str),
        6: ('back_color', str),
        7: ('bold', lambda v: 1 if v.lstrip('-') in ('1', '1.0') else 0),
        8: ('italic', lambda v: 1 if v.lstrip('-') in ('1', '1.0') else 0),
        15: ('border_style', int),
        16: ('outline_width', float),
        17: ('shadow', float),
        18: ('alignment', int),
        19: ('margin_l', int),
        20: ('margin_r', int),
        21: ('margin_v', int),
    }
    result = {}
    for idx, (key, conv) in field_map.items():
        val = parts[idx]
        if isinstance(conv, type) and issubclass(conv, int):
            result[key] = int(float(val))
        elif isinstance(conv, type) and issubclass(conv, float):
            result[key] = float(val)
        elif callable(conv):
            result[key] = conv(val)
        else:
            result[key] = conv(val)
    return result


def generate_ass(df, columns, output_path, style_config, video_resolution=None):
    scale_mode = style_config.get('scale_mode', 'absolute')

    if scale_mode == 'absolute':
        if video_resolution is None:
            video_resolution = (1920, 1080)
        play_res_x, play_res_y = video_resolution
    else:
        play_res_x = style_config.get('play_res_x', 1920)
        play_res_y = style_config.get('play_res_y', 1080)

    src_style = style_config.get('source', {})
    trans_style = style_config.get('translation', {})

    style_lines = []
    style_names = []
    has_source = 'Source' in columns
    has_translation = 'Translation' in columns

    if has_source:
        style_lines.append(_build_style_line('source', src_style))
        style_names.append('Source')
    if has_translation:
        style_lines.append(_build_style_line('translation', trans_style))
        style_names.append('Translation')

    header = (
        "[Script Info]\n"
        f"Title: VideoLingo Generated\n"
        f"ScriptType: v4.00+\n"
        f"PlayResX: {play_res_x}\n"
        f"PlayResY: {play_res_y}\n"
        f"ScaledBorderAndShadow: yes\n"
        f"WrapStyle: 0\n"
        f"\n"
        f"[V4+ Styles]\n"
        f"Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        + "\n".join(style_lines) + "\n"
        f"\n"
        f"[Events]\n"
        f"Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )

    events = []
    for idx, row in df.iterrows():
        ts_str = row['timestamp']
        start_sec, end_sec = _srt_timestamp_to_seconds(ts_str)
        start_ass = seconds_to_ass_time(start_sec)
        end_ass = seconds_to_ass_time(end_sec)

        if len(columns) == 1:
            col = columns[0]
            text = str(row[col]).strip()
            style_name = 'Source' if col == 'Source' else 'Translation'
        else:
            parts = []
            style_name = columns[0].capitalize() if columns[0] == 'Source' else 'Translation'
            if 'Source' in columns and 'Translation' in columns:
                style_name = 'Source'
            for col in columns:
                val = str(row[col]).strip()
                parts.append(val)
            text = '\\N'.join(parts)

        events.append(
            f"Dialogue: 0,{start_ass},{end_ass},{style_name},,0,0,0,,{text}"
        )

    content = header + "\n".join(events) + "\n"

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)