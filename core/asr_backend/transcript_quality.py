import re

from core.utils.config_utils import load_key


def _normalize(value):
    return re.sub(r"[^\w']+", '', str(value).lower(), flags=re.UNICODE)


def find_repetition_loops(words, min_cycles=12, max_period=4):
    """Return obvious contiguous periodic loops in a word sequence."""
    tokens = [_normalize(word) for word in words]
    loops = []
    i = 0
    while i < len(tokens):
        match = None
        for period in range(1, max_period + 1):
            if i + period * min_cycles > len(tokens):
                break
            pattern = tokens[i:i + period]
            if not all(pattern):
                continue
            end = i + period
            while end + period <= len(tokens) and tokens[end:end + period] == pattern:
                end += period
            cycles = (end - i) // period
            if cycles >= min_cycles and (match is None or end > match['end_index']):
                match = {
                    'start_index': i,
                    'end_index': end,
                    'pattern': pattern,
                    'cycles': cycles,
                }
        if match:
            loops.append(match)
            i = match['end_index']
        else:
            i += 1
    return loops


def validate_transcript_quality(df):
    try:
        max_cycles = int(load_key('whisper.max_repetition_cycles'))
    except KeyError:
        max_cycles = 12
    if max_cycles <= 0 or df.empty:
        return
    loops = find_repetition_loops(df['text'].tolist(), min_cycles=max_cycles)
    if not loops:
        return
    examples = ', '.join(
        f"{' '.join(loop['pattern'])!r} x{loop['cycles']}"
        for loop in loops[:3]
    )
    raise RuntimeError(
        f"ASR quality check found {len(loops)} repetition loop(s): {examples}. "
        "Review the Whisper output/settings before starting paid LLM steps, or set "
        "whisper.max_repetition_cycles to 0 to disable this guard."
    )
