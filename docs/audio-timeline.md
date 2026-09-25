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

## Demucs stems start late (fixed in BUILDER-305)

With vocal separation on, word timestamps came out about 60 ms late, because
`vocal.mp3` started 953 samples (16 kHz) after `raw.mp3`. Two MP3 encoder delays
were being counted as audio:

- Demucs' `separate_audio_file()` reads with sphn first. sphn keeps the LAME
  priming of `raw.mp3` (1,105 samples at 32 kHz, about 35 ms).
- `demucs.audio.save_audio` encodes MP3 with lameenc, which writes no LAME/Xing
  header, so decoders cannot trim its own priming (1,105 samples at 44.1 kHz,
  about 25 ms).

`demucs_vl` now decodes `raw.mp3` with FFmpeg (`demucs.audio.AudioFile`, which trims
the delay) and writes each stem through FFmpeg's libmp3lame (its header lets
FFmpeg, pydub and soundfile trim the delay). Both stems start sample-aligned with
`raw.mp3`. This also applies to the WhisperX backend, `background.mp3` in the
dubbing mix and the reference clips cut from `vocal.mp3`. `qwen_asr_local.match_length`
still pads or trims the tail, whose decoded length can differ by a frame.

`tests/test_demucs_vl.py` runs the real FFmpeg and Demucs I/O with the separation
model faked. It checks a lag of at most one 16 kHz sample for both stems, after
the pydub re-export in `_2_asr`, and through soundfile. The same checks against
the previous code measure 953 samples. Stems already in `output/audio/` are reused
as they are, so delete `vocal.mp3` and `background.mp3` (or start a new task) to
regenerate them. The ASR cache schema was bumped to 2, so results transcribed
from the old stems are not reused.
