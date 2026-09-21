# Preserve source audio timing during extraction

## Defect

The ASR input must follow the video's presentation clock. Decoding audio packets
into contiguous samples is not sufficient when packet timestamps contain gaps
or overlap. A compressed frame may decode to 1,024 samples while its container
duration is shorter. Concatenating every decoded sample expands the recognition
clock, so correctly aligned words produce increasingly late subtitles.

This is an existing extraction limitation, not a translation prompt issue.
The FFmpeg extraction command at upstream commit `6e85833` (2024-11-14,
`core/all_whisper_methods/whisperX_utils.py`) already resampled to 16 kHz without
timestamp reconciliation. The recent dependency update did not change that
extraction command. Some inputs with continuous timestamps are unaffected.

## Fix

Apply `aresample=async=1:first_pts=0` before encoding the recognition input,
including MP3 and PCM fallback paths for video and audio-only uploads. FFmpeg
reconciles sample output against timestamps rather than blindly concatenating
frames. No model, subtitle timing heuristic, or translation change is required.

## Validation

```sh
python -m pytest -q tests/test_audio_timeline.py
```

The tests exercise real extraction function bodies without importing ML models.
Synthetic PCM media covers a continuous clock, repeated overlaps and repeated
gaps. The real FFmpeg test compares decoded output duration to source frame
presentation times and demonstrates the old contiguous decode differs by more
than 0.8 seconds on discontinuous inputs. It requires FFmpeg and ffprobe and makes
no network calls. Mocked tests cover all four encoder/input combinations.

## Existing results

Existing recognition audio is retained by the resume mechanism. This fix applies
to newly extracted audio; restarting the application alone does not replace cached
audio or regenerate subtitles. Existing outputs require explicit regeneration or
an independently validated timestamp repair. Source recording/remuxing defects
may also require correction in their producing tool; this change prevents those
timestamp discontinuities from silently shifting VideoLingo's recognition clock.
