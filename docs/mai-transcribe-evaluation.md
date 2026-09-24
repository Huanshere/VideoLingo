# MAI-Transcribe-2 vs local WhisperX: evaluation (2026-09-24)

Branch `feat/mai-transcribe` (base `origin/main` 9bc3020). Every run used VideoLingo's real
ASR stage (`core/_2_asr.transcribe`, then `process_transcription`) in an isolated working
directory with the transcription cache disabled; scores use the resulting `cleaned_chunks.xlsx`.

## Samples

| Sample | Language | Type | Length | Reference |
|---|---|---|---|---|
| `en_ted_sleep` | en | TED talk, audience laughter | 19 min | TED manual captions |
| `en_podcast_tarlov` | en | Two-person podcast, overlapping speech | 27 min | uploader captions |
| `en_street_future`, `en_street_meaning` | en | Outdoor street interviews, non-native speakers, traffic noise | 5.5 min each | Easy English manual captions |
| `zh_tedx_emotion` | zh (Taiwan Mandarin) | TEDx talk | 15 min | uploader zh-TW captions |
| `zh_mix_embodied` | zh + English terms | Tech interview (embodied AI) | first 30 min | uploader zh-Hans captions |
| `zh_vc_siliconvalley` | zh + dense English terms | VC podcast | first 30 min | uploader zh captions |
| `ja_tedx_words`, `ja_tedx_elephant` | ja | TEDx talks | 19 / 16 min | uploader ja captions |
| `private_long_1..3` | en | Long single-speaker software training recordings (not public) | 75-80 min each | **earlier VideoLingo WhisperX `src.srt` (not ground truth)** |

Variants: `local` = WhisperX large-v3 (zh uses VideoLingo's Belle large-v3 model),
`local_turbo` = large-v3-turbo, `mai_clean` (shipped default), `mai_verbatim`, `mai_auto`
(no forced language). History samples ran `local` and `mai_clean` only.

Metrics: WER for English (fillers such as "uh/um" removed from both sides), CER for zh/ja
(zh normalised to Simplified, punctuation removed). Cue timing = |start of each reference
cue - start of its first matched recognised token|. Download clips of sections (`-t 1800`)
were cut after download; all audio was deleted afterwards.

## Accuracy against manual captions (lower is better)

| Sample | local large-v3 | local turbo | MAI clean | MAI verbatim | MAI auto |
|---|---|---|---|---|---|
| en_ted_sleep | **1.62** | 51.56 | 2.71 | 2.07 | 2.68 |
| en_podcast_tarlov | 9.35 | 41.21 | **7.28** | 7.62 | 7.37 |
| en_street_future | 8.97 | 17.39 | **6.42** | 6.76 | 6.42 |
| en_street_meaning | 12.75 | 32.11 | **11.07** | 11.36 | 11.26 |
| zh_tedx_emotion | 9.60 | 9.60 | **7.47** | 8.14 | 7.47 |
| zh_mix_embodied | 18.08 | 18.08 | **3.22** | 4.14 | 3.33 |
| zh_vc_siliconvalley | 22.59 | 22.59 | **6.26** | 6.40 | 6.26 |
| ja_tedx_words | **10.93** | 66.76 | 11.89 | 13.07 | 12.10 |
| ja_tedx_elephant | 8.31 | 72.34 | 7.35 | **7.21** | 7.37 |

- Chinese is the decisive difference. VideoLingo's local zh model transliterates English
  terms into Chinese sound-alikes or drops them: `安特劳佩克` for Anthropic, `欧本内` for OpenAI,
  `赛克` for cycle, `巨神` for 具身 (embodied). MAI keeps `Anthropic`, `OpenAI`, `AI agent`,
  `SPV`, `Lydia` and writes 具身 correctly. Most of the local error is deletions
  (1,407 of 1,881 errors on `zh_mix_embodied`).
- Clean English speech: local large-v3 is slightly better (TED 1.6% vs 2.1-2.7%).
- Noisy, overlapping or non-native English: MAI is better by 1.5-2.5 points.
- Japanese: a tie (one sample each way, within about 1 point).
- `local_turbo` is unusable in this pipeline for en/ja: it loops on one word
  (`sleep, sleep, sleep...`, `like, like, like...`) for long stretches, producing 17-72% error.
  For zh the setting has no effect because VideoLingo forces the Belle model.
  `repetition_penalty 1.1` + `no_repeat_ngram_size 3` only reduced TED to 24% (heavy
  deletions), so the branch maps `large-v3-turbo` to `large-v3` and keeps their cache keys equal.
- History samples (reference = old WhisperX output, so biased toward local): local 0.3-0.9%,
  MAI 1.4-2.7% disagreement. This measures similarity to the old pipeline, not correctness.

## Timing

Median cue-start difference, local vs MAI clean (ms): en_podcast 245/238, street 288/270 and
131/140, zh 159/163, 305/315, 30/34, ja 121/123 and 30/34. Both engines place cues
equally well; differences are within one video frame at the median. `en_ted_sleep` shows
~12 s for every engine because the TED caption file is offset from this download (intro
trimmed), so its timing row is excluded. The earlier word-level comparison on history
03/05/06 gave a 25 ms median word-start difference between the engines.

Recognised tokens inside reference silences of 3 s or more (hallucination proxy) were 0-2 for
both engines on every sample except the offset TED file.

## Language detection, punctuation, numbers

- `mai_auto` detected the right language on all 9 external samples; accuracy matched forced
  language within 0.2 points. Local WhisperX also detected correctly once its model was cached.
- Sentence-final punctuation: local zh/ja output is almost unpunctuated (0-2% of tokens end a
  sentence); MAI ends 3-4%. Local ja/zh numbers are written as Chinese numerals
  (`一百零六`), so number-string matches were 0-11% vs 43-100% for MAI.
- `clean` vs `verbatim`: nearly identical except verbatim inserts fillers; clean is the better
  default for subtitles.

## Speed, reliability and cost

- Per 30 min of audio MAI took 40-50 s; local large-v3 took 50-100 s on an RTX 4000 Ada
  (Belle zh 97-455 s including cold model loads).
- Long audio: the 75-80 min history files needed 3-4 HTTP attempts each; the service drops
  the connection (`RemoteDisconnected`) on some long uploads. The built-in retry recovered
  every case. One 01 run took 549 s because of the retries. Files up to 30 min never failed.
- MAI usage for this evaluation: about 12 audio hours, roughly USD 1.2 at the USD 0.10/hour
  preview price; covered by Azure trial credit.

## Conclusion

MAI-Transcribe-2 is a worthwhile optional backend: equal word timing, faster, no GPU, and
markedly better on Chinese (especially mixed Chinese-English) and on noisy or conversational
English. Local WhisperX remains marginally better on clean studio English. Limitations: public
preview (no SLA), Azure account and key required, and long uploads need the retry path.

Reference captions from uploaders are not independently verified; the history comparison is
self-referential; the full translate/dub pipeline was not run on these outputs.
