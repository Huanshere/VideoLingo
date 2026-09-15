"""Expose FFmpeg DLLs to native Python extensions on Windows."""

import os
import shutil
from pathlib import Path

_dll_handles = []


def configure_ffmpeg_dlls():
    """Use the same FFmpeg directory as the application's command-line calls."""
    if os.name != "nt" or _dll_handles:
        return
    executable = shutil.which("ffmpeg")
    if executable:
        # Python 3.8+ does not use PATH alone for extension dependency lookup.
        # Keep the handle alive for the lifetime of the process.
        _dll_handles.append(os.add_dll_directory(str(Path(executable).resolve().parent)))
