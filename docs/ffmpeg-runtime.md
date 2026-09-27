# Managed FFmpeg runtime

The default Qwen installation requires no manual FFmpeg download, package-manager
command, administrator permission, or system PATH change. Run `setup_env.py` as
documented in the README. Its `installer.py` stage installs `static-ffmpeg==3.0`
and fetches FFmpeg and ffprobe automatically. The binaries live inside that
Python environment's `static_ffmpeg/bin` directory.

The provider offers Windows x86_64, Linux x86_64/aarch64 and macOS Intel/Apple
Silicon binaries. VideoLingo's own platform requirements still apply (notably
macOS 14+ Apple Silicon for the default MLX stack). This is automatic provisioning,
not removal of the FFmpeg engine. Setup needs access to PyPI and the provider's
GitHub download URLs. A download failure fails setup with a retry instruction;
rerun `python installer.py` once connectivity is restored. Partial downloads
without both tools are fetched again, including a read/execute-only executable
left by an interrupted extraction. Normal imports, app launch and `--check`
never download, so installed media tools work offline.

`runtime_libraries.configure_ffmpeg()` prepends the managed directory to the
current process PATH before application dependencies are imported. Child
processes inherit it. This covers Qwen decoding, Demucs' AudioFile, pydub
(including ffprobe), yt-dlp, subtitle rendering, speed adjustment and mixing.
The installer checks both programs, required filters, and MP3/AAC/H.264/PCM
encoders. NVENC remains optional and also requires compatible hardware/drivers.

## Overrides and WhisperX

For a custom deployment, set `VIDEOLINGO_FFMPEG_DIR` to a directory containing
both executables before launch. This explicit override disables managed downloads
and is checked by the same validation. A random system FFmpeg on PATH never
silently overrides the application's managed tools.

Both Qwen and VideoLingo's WhisperX pipeline use the managed CLI. WhisperX
passes decoded waveforms to pyannote and alignment, so it does not need
TorchCodec's FFmpeg shared-library decoder. `installer.py --check` exercises
WhisperX CLI decoding and pyannote waveform handling only when that backend is
selected. It downloads no models. See the [WhisperX guide](pages/docs/whisperx-manual.en-US.md#ffmpeg-runtime)
for the distinction from custom code that passes filenames directly to pyannote.
The optional Windows shared-DLL override remains available for custom usage.

Do not test installation by running `ffmpeg -version` in a new system terminal:
the application intentionally does not modify that terminal's PATH. Use the
environment's `python installer.py --check` instead.

## Validation

The Windows experiment used a fresh Python 3.13 environment and downloaded
FFmpeg 8.0.1 automatically through static-ffmpeg 3.0. `installer.check_ffmpeg()`
was also run with an empty PATH and a fresh provider cache: download, extraction
and validation all passed. A real one-second H.264 NVENC encode passed on an
RTX 5060 Laptop GPU with the managed executable and no system tools on PATH.
The automated runtime test
starts a child Python with an empty PATH and disables Python socket connections.
It verifies that neither tool exists before initialization, then checks managed
tool discovery, pydub MP3 export/read, ffprobe metadata, atempo conversion,
Qwen's actual audio decoder and yt-dlp's FFmpeg/ffprobe discovery.
The media regression suite additionally covers extraction quality, discontinuous
timestamps, loudness and final subtitle/audio/video synthesis.

Windows validation on 2026-09-27 (Python 3.13.5, Torch 2.8.0+cu128,
qwen-asr 0.0.6, Demucs 4.1.0):

- Full suite with system PATH cleared before managed-runtime initialization:
  **349 passed, 4 skipped, 6 subtests passed**. Skips: two opt-in paid pipeline
  tests, live-server test, and the PowerShell-dependent test with no system PATH.
- `uv pip check`: all installed packages compatible. The real installer health
  check passed with Demucs required and cu128 selected; TorchCodec was absent.
- Real Qwen3-ASR **0.6B** + ForcedAligner-0.6B inference on the public
  [Qwen English sample](https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen3-ASR-Repo/asr_en.wav):
  15.05125 s input, 36 timestamped words, 17.83 s elapsed including model loading
  in the ASR/aligner calls. Models came from the local Hugging Face cache with
  Hub/Transformers offline mode; system PATH was empty before initialization.
  Word starts were monotonic and all word intervals stayed within the input.
  This validates the real decoder/model/aligner path, not translation APIs or
  subjective transcription accuracy. The 1.7B model was not exercised here.

Run the targeted offline checks after setup:

```bash
python -m pytest tests/test_ffmpeg_runtime.py tests/test_dependencies.py tests/test_qwen_asr_local.py tests/test_audio_extract_quality.py tests/test_audio_timeline.py tests/test_dubbing_loudness.py
```

macOS validation on 2026-09-27 used an Apple Silicon arm64 Mac (macOS 26.6.2,
16 GiB) with a new Python 3.13.15 environment. The documented `setup_env.py`
flow, using `--path` to keep the environment in a separate verification directory,
installed Torch 2.8.0, mlx-audio 0.5.6, Demucs 4.1.0 and static-ffmpeg 3.0.
`installer.py` downloaded and extracted both tools without Homebrew or a manual
FFmpeg installation. The macOS provider archive supplied **FFmpeg 7.0** (the
provider's URL contains `v8.0`, but the binaries report 7.0); `file` and `lipo`
identified both as native Mach-O arm64, and they executed without changing macOS
security settings. With a child process PATH limited to system command directories,
neither tool was discoverable before `configure_ffmpeg()`. Afterwards, both resolved
inside this environment's `static_ffmpeg/bin/darwin_arm64` directory. The separate
WhisperX environment downloaded its own managed pair to the same package-relative
location. `installer.py --check --require-demucs` passed with network access denied.

The same network-denied process exported and read MP3 through pydub, read metadata
with ffprobe, ran atempo, loudnorm and amix, encoded H.264/AAC, and burned an ASS
subtitle. libass selected `/System/Library/Fonts/Helvetica.ttc`; the subtitle was
visible in the encoded frame. yt-dlp discovered both managed tools. Demucs' real
audio reader/writer path passed the stem alignment tests (separation model mocked).
The full default-environment suite with system FFmpeg excluded passed **354 tests,
6 skipped, 6 subtests passed**. Skips covered two opt-in API pipeline tests, a
live-server test, the optional WhisperX test in the default MLX environment, and
two Windows-only checks. `pip check` found no broken requirements.

The default **MLX Qwen3-ASR 1.7B** model and ForcedAligner-0.6B, reused from a
complete local Hugging Face cache, processed the 15.051 s public English sample
with network access denied: 37 words with valid monotonic timestamps, 7.95 s for
the backend call. The managed FFmpeg CLI decoded the sample. The separate stable
WhisperX 3.8.6 environment used Torch 2.8.0, pyannote-audio 4.0.7 and TorchCodec
0.7.0. Importing TorchCodec's native decoder failed because `libavutil.59.dylib`
was absent, while `check_whisperx_runtime()` passed with an in-memory waveform.
The optional-backend regression test also passed in that separate environment
with TorchCodec imports deliberately blocked.
The real tiny.en CPU backend then ran its default pyannote VAD and English alignment
on that sample: 35 timestamped words. Once tiny.en and the alignment model were
cached in the separate verification directory, a network-denied repeat passed in
1.49 s. WhisperX remains a manual **Python dependency** in a separate Apple
Silicon environment because its Hugging Face Hub constraint conflicts with MLX;
it did not require a manually installed FFmpeg CLI or shared libraries for this
pipeline. No paid translation/TTS API, live YouTube download, NVENC or larger
WhisperX model was exercised. Linux binaries remain untested here.

The macOS run also exposed and fixed an interrupted-cache edge case: the provider's
read/execute-only `ffmpeg` could survive without `ffprobe`, and extraction could
not overwrite it. Setup now removes the incomplete managed pair before fetching
again. A regression test covers this, and a temporary-cache exercise verified
missing-tool and download-failure messages plus successful re-extraction. Only
the new verification cache was modified.

Provider: https://github.com/zackees/static_ffmpeg (version 3.0).
The alternative ffmpeg-binaries 1.1.0 was inspected but not adopted: its Windows
wheel contained FFmpeg 6.0, while static-ffmpeg supplied 8.0.1 in this experiment.

### WhisperX follow-up validation

With WhisperX 3.8.6, pyannote-audio 4.0.7 and TorchCodec 0.7.0 installed in the
same isolated Windows environment, system PATH was cleared before initialization.
Importing `torchcodec.decoders` raised RuntimeError, confirming that no working
shared-library decoder was available. The actual `whisperX_local.transcribe_audio`
entry point then decoded the same 15.05125 s sample using managed FFmpeg 8.0.1,
ran tiny.en on CPU with the default pyannote VAD, and aligned 35 words with
WAV2VEC2_ASR_BASE_960H. ASR took 0.65 s and alignment 1.26 s; the complete call
including model acquisition/loading took 24.68 s. All timestamped word intervals
stayed within the input. The experiment overrode only model/language/device and
configuration persistence, not VAD, decoding, recognition or alignment.
Large/Belle models, WhisperX GPU execution and other operating systems were not
validated in this follow-up. The automated optional-backend regression also
blocks TorchCodec imports explicitly and verifies the new waveform health check.
After this change, the full suite with system PATH cleared passed **350 tests,
4 skipped, 6 subtests passed**. `uv pip check` reported all 238 installed packages
compatible. The real installer health check also passed with WhisperX selected,
Demucs required and the cu128 Torch build.
After rebasing onto #621 at `bf6e4e4`, the same full-suite run passed **356 tests,
4 skipped, 6 subtests passed**.
