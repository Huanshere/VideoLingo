"""Create a VideoLingo Python environment, then run the stage-based installer.

Default behavior creates a project-local ``.venv``. Use ``--shared`` to create
or reuse ``~/.venvs/videolingo`` so multiple VideoLingo checkouts share the same
heavy dependencies (PyTorch, WhisperX, Demucs, etc.).
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


PYTHON_VERSION = "3.13"
SCRIPT_DIR = Path(__file__).resolve().parent
LOCAL_VENV = SCRIPT_DIR / ".venv"
SHARED_VENV = Path.home() / ".venvs" / "videolingo"


def run(cmd: list[str], check: bool = True, **kwargs) -> subprocess.CompletedProcess:
    print("  > " + " ".join(str(x) for x in cmd))
    return subprocess.run(cmd, check=check, **kwargs)


def is_uv_installed() -> bool:
    return shutil.which("uv") is not None


def install_uv() -> None:
    print("\n[1/3] Checking uv")
    if is_uv_installed():
        ver = subprocess.run(["uv", "--version"], capture_output=True, text=True).stdout.strip()
        print(f"  uv is already installed: {ver}")
        return

    if platform.system() == "Windows":
        methods = [
            ["winget", "install", "astral-sh.uv", "--accept-package-agreements", "--accept-source-agreements"],
            ["powershell", "-ExecutionPolicy", "ByPass", "-c", "irm https://astral.sh/uv/install.ps1 | iex"],
            [sys.executable, "-m", "pip", "install", "uv"],
        ]
    else:
        methods = [
            ["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"],
            [sys.executable, "-m", "pip", "install", "uv"],
        ]

    for cmd in methods:
        try:
            run(cmd)
            add_uv_to_path()
            if is_uv_installed():
                print("  uv installed successfully")
                return
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("  install method failed, trying next method...")

    raise SystemExit("ERROR: uv could not be installed. Install it manually: https://docs.astral.sh/uv/")


def add_uv_to_path() -> None:
    candidates = [
        Path.home() / ".local" / "bin",
        Path.home() / ".cargo" / "bin",
        Path(os.environ.get("LOCALAPPDATA", "")) / "uv" / "bin",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "uv",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Links",
    ]
    name = "uv.exe" if platform.system() == "Windows" else "uv"
    for path in candidates:
        if (path / name).is_file():
            os.environ["PATH"] = str(path) + os.pathsep + os.environ.get("PATH", "")
            return


def venv_python(venv_path: Path) -> Path:
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"


def venv_bin(venv_path: Path) -> Path:
    if platform.system() == "Windows":
        return venv_path / "Scripts"
    return venv_path / "bin"


def python_version_ok(python_exe: Path) -> bool:
    if not python_exe.is_file():
        return False
    result = subprocess.run([str(python_exe), "--version"], capture_output=True, text=True)
    return f"Python {PYTHON_VERSION}." in (result.stdout or result.stderr)


def create_venv(path: Path, yes: bool = False) -> Path:
    print(f"\n[2/3] Creating/reusing virtual environment: {path}")
    python_exe = venv_python(path)
    if python_version_ok(python_exe):
        result = subprocess.run([str(python_exe), "--version"], capture_output=True, text=True)
        print(f"  Reusing existing venv: {result.stdout.strip() or result.stderr.strip()}")
        return python_exe

    if path.exists():
        if not yes:
            answer = input(f"  Existing venv at {path} is not Python {PYTHON_VERSION}. Remove and recreate it? [y/N] ").strip().lower()
            if answer != "y":
                raise SystemExit("Cancelled.")
        shutil.rmtree(path, ignore_errors=True)

    path.parent.mkdir(parents=True, exist_ok=True)
    run(["uv", "venv", "--seed", "--python", PYTHON_VERSION, str(path)], cwd=SCRIPT_DIR)
    if not python_version_ok(python_exe):
        raise SystemExit(f"ERROR: failed to create a Python {PYTHON_VERSION} virtual environment")
    return python_exe


def run_installer(python_exe: Path, args: argparse.Namespace) -> None:
    print("\n[3/3] Installing VideoLingo dependencies")
    env = os.environ.copy()
    env["PATH"] = str(venv_bin(python_exe.parent.parent)) + os.pathsep + env.get("PATH", "")
    cmd = [str(python_exe), str(SCRIPT_DIR / "installer.py"), "--yes"]
    if args.auto_mirror:
        cmd.append("--auto-mirror")
    if args.force:
        cmd.append("--force")
    if args.upgrade:
        cmd.append("--upgrade")
    if args.skip_demucs:
        cmd.append("--skip-demucs")
    if args.require_demucs:
        cmd.append("--require-demucs")
    run(cmd, cwd=SCRIPT_DIR, env=env)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create and install a VideoLingo environment")
    parser.add_argument("--shared", action="store_true", help=f"use shared venv at {SHARED_VENV}")
    parser.add_argument("--path", help="custom venv path; implies --shared-style external venv")
    parser.add_argument("--skip-install", action="store_true", help="only create/reuse the venv")
    parser.add_argument("--auto-mirror", action="store_true", help="auto-select a PyPI mirror before install")
    parser.add_argument("--skip-demucs", action="store_true", help="skip optional Demucs install")
    parser.add_argument("--require-demucs", action="store_true", help="fail if Demucs cannot be installed")
    parser.add_argument("--force", action="store_true", help="force reinstall staged packages")
    parser.add_argument("--upgrade", action="store_true", help="refresh dependencies within compatibility bounds")
    parser.add_argument("--yes", action="store_true", help="non-interactive; recreate wrong-version venvs")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    target = Path(args.path).expanduser() if args.path else (SHARED_VENV if args.shared else LOCAL_VENV)

    print("=" * 60)
    print("  VideoLingo Environment Setup")
    print("=" * 60)
    print(f"  Project dir : {SCRIPT_DIR}")
    print(f"  Python ver  : {PYTHON_VERSION}")
    print(f"  Venv path   : {target}")

    install_uv()
    python_exe = create_venv(target, yes=args.yes)

    if args.skip_install:
        print("\n  --skip-install: dependencies were not installed")
        print(f"  To install later: {python_exe} {SCRIPT_DIR / 'installer.py'} --yes")
    else:
        run_installer(python_exe, args)

    print("\n" + "=" * 60)
    print("  Setup complete")
    print("=" * 60)
    if platform.system() == "Windows":
        print("  Start with: OneKeyStart.bat")
    else:
        streamlit = venv_bin(target) / "streamlit"
        print(f"  Start with: {streamlit} run st.py")


if __name__ == "__main__":
    main()
