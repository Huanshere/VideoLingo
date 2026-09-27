# /// script
# requires-python = "==3.12.*"
# dependencies = []
# ///
"""Install VideoLingo when needed, then start it with its project environment."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
PYTHON = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def main() -> int:
    healthy = PYTHON.is_file() and subprocess.run(
        [str(PYTHON), "installer.py", "--quick-check", "--quiet"], cwd=ROOT
    ).returncode == 0

    if not healthy:
        print("Installing or repairing VideoLingo...")
        result = subprocess.run(
            [sys.executable, "setup_env.py", "--yes"], cwd=ROOT
        )
        if result.returncode:
            return result.returncode

    if not PYTHON.is_file():
        print("ERROR: VideoLingo's Python environment was not created.")
        return 1

    return subprocess.run(
        [str(PYTHON), "-m", "streamlit", "run", "st.py"], cwd=ROOT
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
