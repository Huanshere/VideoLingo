"""Conservative speech boundaries; keep pauses and the original sample timeline."""

SPEECH_PADDING_SECONDS = 1.0


def _speech_regions(audio, sample_rate):
    import torch
    from core.utils import check_cancel

    # Importing silero_vad changes PyTorch's process-wide thread count. Restore it
    # before ASR runs, including when loading or inference fails.
    threads = torch.get_num_threads()
    try:
        torch.set_num_threads(1)
        from silero_vad import load_silero_vad, get_speech_timestamps

        model = load_silero_vad()
        return get_speech_timestamps(
            torch.from_numpy(audio), model, sampling_rate=sample_rate,
            threshold=0.35, min_speech_duration_ms=100, speech_pad_ms=0,
            progress_tracking_callback=lambda _: check_cancel(),
        )
    finally:
        torch.set_num_threads(threads)


def trim_speech_windows(audio, windows, sample_rate=16000):
    """Trim only window edges, padding both sides to retain soft/short words.

    A window with no detected speech is left intact: VAD missing quiet speech
    must not silently discard it. Internal pauses are never removed. Returned
    indices still refer to the original audio, for both ASR and alignment.
    """
    if not len(audio) or not windows:
        return windows
    regions = _speech_regions(audio, sample_rate)
    padding = round(SPEECH_PADDING_SECONDS * sample_rate)
    trimmed = []
    for start, end in windows:
        speech = [r for r in regions if r["end"] > start and r["start"] < end]
        if not speech:
            trimmed.append((start, end))
            continue
        trimmed.append((max(start, speech[0]["start"] - padding),
                        min(end, speech[-1]["end"] + padding)))
    return trimmed
