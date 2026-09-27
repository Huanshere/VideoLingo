"""Application-owned FFmpeg CLI and optional WhisperX shared libraries.

Only setup downloads binaries. Imports and health checks are offline, and PATH
changes affect this process and its children, never the user's system settings.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path

_dll_handles = []


def configure_ffmpeg(*, download=False, required=False):
    """Select the managed CLI pair, or an explicit VIDEOLINGO_FFMPEG_DIR.

    `required=False` permits importing core utilities while setup is still
    installing dependencies. App entry points and health checks require it.
    """
    override = os.environ.get("VIDEOLINGO_FFMPEG_DIR")
    try:
        if override:
            directory = Path(override).expanduser().resolve()
        else:
            machine = platform.machine().lower()
            if (sys.platform, machine) not in {
                ("win32", "amd64"), ("win32", "x86_64"),
                ("darwin", "arm64"), ("darwin", "x86_64"),
                ("linux", "x86_64"), ("linux", "aarch64"), ("linux", "arm64"),
            }:
                raise OSError(f"No managed FFmpeg build for {sys.platform}/{machine}")
            from static_ffmpeg.run import get_platform_dir, get_or_fetch_platform_executables_else_raise
            directory = Path(get_platform_dir())
            if download:
                # Repair interrupted installs where the marker survived but a tool did not.
                suffix = ".exe" if sys.platform == "win32" else ""
                if not all((directory / (name + suffix)).is_file() for name in ("ffmpeg", "ffprobe")):
                    (directory / "installed.crumb").unlink(missing_ok=True)
                get_or_fetch_platform_executables_else_raise()
        suffix = ".exe" if sys.platform == "win32" else ""
        if not all((directory / (name + suffix)).is_file() for name in ("ffmpeg", "ffprobe")):
            raise FileNotFoundError(f"FFmpeg/ffprobe pair missing in {directory}")
    except (ImportError, OSError) as exc:
        if required or download or override:
            raise RuntimeError("FFmpeg runtime is not ready. Run python installer.py to install it automatically. "
                               f"Details: {exc}") from exc
        return None
    paths = os.environ.get("PATH", "").split(os.pathsep)
    os.environ["PATH"] = os.pathsep.join([str(directory), *(p for p in paths if p != str(directory))])
    # pydub may already have been imported by an embedding application.
    if "pydub" in sys.modules:
        sys.modules["pydub"].AudioSegment.converter = str(directory / ("ffmpeg" + suffix))
    return directory


def validate_ffmpeg():
    """Check both executables and the codecs/filters the actual pipeline needs."""
    directory = configure_ffmpeg(required=True)
    suffix = ".exe" if sys.platform == "win32" else ""

    def output(tool, *args):
        return subprocess.run([str(directory / (tool + suffix)), "-hide_banner", *args],
                              check=True, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=30).stdout

    version = output("ffmpeg", "-version").splitlines()[0]
    output("ffprobe", "-version")
    for option, needed in (
        ("-filters", {"subtitles", "scale", "pad", "aresample", "atempo", "loudnorm", "volume", "amix"}),
        ("-encoders", {"libmp3lame", "aac", "libx264", "pcm_s16le", "pcm_s24le"}),
    ):
        available = {line.split()[1] for line in output("ffmpeg", option).splitlines() if len(line.split()) >= 2}
        missing = needed - available
        if missing:
            raise RuntimeError(f"FFmpeg {option} missing: {', '.join(sorted(missing))}")
    return version


def check_whisperx_runtime():
    """Exercise WhisperX's CLI-to-waveform path without models or downloads.

    pyannote accepts in-memory audio even when TorchCodec's shared-library
    decoder cannot load. Probe that supported path, as used by our backend.
    """
    import tempfile
    import wave
    import warnings

    configure_ffmpeg(required=True)
    configure_ffmpeg_dlls()
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=r"\ntorchcodec is not installed correctly.*")
        from whisperx.asr import load_model  # noqa: F401: load the optional backend dependencies
        from whisperx.audio import load_audio
        from pyannote.audio.core.io import Audio
        import torch

    with tempfile.TemporaryDirectory() as directory:
        filename = str(Path(directory) / "probe.wav")
        with wave.open(filename, "wb") as stream:
            stream.setnchannels(1)
            stream.setsampwidth(2)
            stream.setframerate(16000)
            stream.writeframes(b"\x00\x00" * 1600)
        decoded = load_audio(filename)
    waveform, sample_rate = Audio(sample_rate=16000)(
        {"waveform": torch.from_numpy(decoded).unsqueeze(0), "sample_rate": 16000}
    )
    if sample_rate != 16000 or tuple(waveform.shape) != (1, 1600):
        raise RuntimeError("WhisperX waveform decoding check returned unexpected audio")


def configure_ffmpeg_dlls():
    """Find optional WhisperX DLLs independently of the managed static CLI."""
    if os.name != "nt" or _dll_handles:
        return
    explicit = os.environ.get("VIDEOLINGO_FFMPEG_DLL_DIR")
    directories = [explicit] if explicit else os.environ.get("PATH", "").split(os.pathsep)
    for item in directories:
        if not item:
            continue
        directory = Path(item)
        if not directory.is_dir() or not any(directory.glob("avcodec-*.dll")):
            continue
        # Python 3.8+ does not use PATH alone for extension dependency lookup.
        # Keep the handle alive for the lifetime of the process.
        _dll_handles.append(os.add_dll_directory(str(directory.resolve())))
        break
