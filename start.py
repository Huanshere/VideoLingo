# /// script
# requires-python = "==3.12.*"
# dependencies = []
# ///
"""Install VideoLingo when needed, then start it with its project environment."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LOCAL_VENV = ROOT / ".venv"
SHARED_VENV = Path.home() / ".venvs" / "videolingo"
PYTHON_RELATIVE = "Scripts/python.exe" if os.name == "nt" else "bin/python"


def is_python_312(python: Path) -> bool:
    if not python.is_file():
        return False
    try:
        return subprocess.run(
            [str(python), "-c", "import sys; sys.exit(sys.version_info[:2] != (3, 12))"],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode == 0
    except OSError:
        return False


def is_healthy(python: Path) -> bool:
    return subprocess.run(
        [str(python), "installer.py", "--quick-check", "--quiet"], cwd=ROOT
    ).returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Install if needed, then start VideoLingo")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--api", action="store_true", help="start the local HTTP API instead of the web UI")
    mode.add_argument("--check", action="store_true", help="check the environment without installing or launching")
    args = parser.parse_args()

    candidates = [(venv, venv / PYTHON_RELATIVE) for venv in (SHARED_VENV, LOCAL_VENV)]
    selected = next(((venv, exe) for venv, exe in candidates if is_python_312(exe)), None)

    if args.check:
        if selected is None:
            print("ERROR: No VideoLingo Python 3.12 environment found. Run uv run start.py to install it.")
            return 1
        _, python = selected
        return subprocess.run([str(python), "installer.py", "--check"], cwd=ROOT).returncode

    if selected is None or not is_healthy(selected[1]):
        target = selected[0] if selected else LOCAL_VENV
        python = target / PYTHON_RELATIVE
        print("Installing or repairing VideoLingo...")
        setup = [sys.executable, "setup_env.py", "--yes"]
        if target == SHARED_VENV:
            setup.append("--shared")
        result = subprocess.run(
            setup, cwd=ROOT
        )
        if result.returncode:
            return result.returncode
    else:
        _, python = selected

    if not python.is_file():
        print("ERROR: VideoLingo's Python environment was not created.")
        return 1

    command = ["api.py"] if args.api else ["-m", "streamlit", "run", "st.py"]
    return subprocess.run([str(python), *command], cwd=ROOT).returncode


if __name__ == "__main__":
    raise SystemExit(main())
