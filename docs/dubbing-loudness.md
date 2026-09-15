# Dubbing loudness: bounded improvement for issue 533

Issue 533 reports changing perceived distance and disconnected sentences after an
upgrade. Its previous version, exact Fish backend, source artifacts and historical
provider outputs are unknown. This change addresses a reproduced local mechanism,
not a confirmed complete explanation of that report.

## Historical findings

- v2.0.x used the direct Fish endpoint; v2.1.0 switched to the 302 Fish endpoint.
- v2.2.1 applied the configured dub_volume multiplier (default 1.5). Commit eb8ee4c
  replaced it with whole-file RMS normalization, including silence in the average.
- v2.2.1 to v3.0.0 also reduced final video AAC bitrate from 192k to 96k.
- Fish requests and dubbing assembly did not substantively change between v3.0.0
  and v3.0.1. Synthetic processing produced identical decoded samples for those tags.

## Change

Final video assembly measures the dub with FFmpeg's gated integrated loudness
measurement (`loudnorm`). Quiet/silent blocks are excluded by the standard gate,
so silence does not dilute the average as it did with whole-file RMS. Target is
-20 LUFS, with gain capped to keep the measured true peak at or below -1 dBTP.
Peak headroom takes priority over reaching the loudness target.

A second pass applies only a fixed gain, not dynamic compression. Speech dynamics,
silences, sample rate, channel count and timing are preserved. Unmeasurable silence
or very short audio is passed through with zero gain. The temporary mix input is
24-bit PCM; final video AAC uses 192k again. FFmpeg failure now propagates rather
than printing a success message. Analysis requires one additional full audio pass.

This is scoped to the dubbed track during final video assembly. Original ASR/F5
reference normalization is unchanged. Standalone dub.mp3 remains the original
assembly output. The existing no-burn placeholder and audio-only paths are unchanged.
Background gain and mixing are unchanged. This does not equalize separate TTS
sentences, remove reverberation, join sentence requests, restore lost bandwidth or
reproduce an older remote Fish model. More natural prosody still needs actual speech
comparisons before modifying TTS request segmentation.

## Validation

`python -m pytest tests/test_dubbing_loudness.py -q`

Seven tests use real local FFmpeg and synthetic audio: silence-padding stability
(less than 0.3 dB active-level difference), preserved 12 dB dynamics, peak headroom,
silence, short stereo input, error propagation and actual six-second video assembly
with subtitles/background/dubbing. Frame counts, sample rates and channels are
checked, plus final audio/video durations. Network/model calls are not made. This
establishes signal-processing behavior, not subjective speech quality improvement.
