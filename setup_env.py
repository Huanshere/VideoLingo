"""
VideoLingo Environment Setup (No Anaconda Required)

This script provides a conda-free installation path using `uv` (by Astral).
It automatically:
  1. Installs uv if not found
  2. Creates a .venv with Python 3.10
  3. Runs install.py inside the venv

Usage:
  python setup_env.py          # Full setup (any system Python 3.x works)
  python setup_env.py --skip-install  # Only create venv, don't run install.py
"""

import os
import sys
import shutil
import subprocess
import platform

PYTHON_VERSION = "3.10"
VENV_DIR = ".venv"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def run(cmd, check=True, **kwargs):
    """Run a command and return the CompletedProcess."""
    print(f"  > {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    return subprocess.run(cmd, check=check, **kwargs)


def is_uv_installed():
    """Check if uv is available on PATH."""
    return shutil.which("uv") is not None


def install_uv():
    """Install uv using platform-appropriate method with fallbacks."""
    print("\n[1/3] Installing uv...")

    if is_uv_installed():
        ver = subprocess.run(
            ["uv", "--version"], capture_output=True, text=True
        ).stdout.strip()
        print(f"  uv is already installed: {ver}")
        return

    system = platform.system()
    if system == "Windows":
        _install_uv_windows()
    else:
        # macOS / Linux
        try:
            run(["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"])
        except subprocess.CalledProcessError:
            print("  curl installer failed, trying pip...")
            run([sys.executable, "-m", "pip", "install", "uv"])

    # After installation, uv may not be on PATH in the current session.
    if not is_uv_installed():
        _add_uv_to_path()

    if not is_uv_installed():
        print(
            "\n*** ERROR: uv was installed but not found on PATH. ***\n"
            "Please restart your terminal and run this script again.\n"
            "Or install uv manually: https://docs.astral.sh/uv/getting-started/installation/"
        )
        sys.exit(1)

    ver = subprocess.run(
        ["uv", "--version"], capture_output=True, text=True
    ).stdout.strip()
    print(f"  uv installed successfully: {ver}")


def _install_uv_windows():
    """Try multiple methods to install uv on Windows."""
    methods = [
        ("winget", ["winget", "install", "astral-sh.uv",
                     "--accept-package-agreements", "--accept-source-agreements"]),
        ("PowerShell installer", [
            "powershell", "-ExecutionPolicy", "ByPass", "-c",
            "irm https://astral.sh/uv/install.ps1 | iex"
        ]),
        ("pip", [sys.executable, "-m", "pip", "install", "uv"]),
    ]

    for name, cmd in methods:
        try:
            print(f"  Trying {name}...")
            run(cmd)
            # Check if PATH needs updating after install
            if not is_uv_installed():
                _add_uv_to_path()
            if is_uv_installed():
                return
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"  {name} failed, trying next method...")
            continue

    print("  All installation methods failed.")


def _add_uv_to_path():
    """Try to add uv's default install location to PATH for this session."""
    home = os.path.expanduser("~")
    candidates = [
        os.path.join(home, ".local", "bin"),
        os.path.join(home, ".cargo", "bin"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "uv", "bin"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "uv"),
    ]
    for p in candidates:
        if not os.path.isdir(p):
            continue
        uv_name = "uv.exe" if platform.system() == "Windows" else "uv"
        if os.path.isfile(os.path.join(p, uv_name)):
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]
            return


def create_venv():
    """Create a virtual environment with Python 3.10 using uv."""
    print(f"\n[2/3] Creating virtual environment with Python {PYTHON_VERSION}...")

    venv_path = os.path.join(SCRIPT_DIR, VENV_DIR)

    if os.path.exists(venv_path):
        # Check if existing venv has the right Python version
        python_exe = _get_venv_python(venv_path)
        if python_exe and os.path.isfile(python_exe):
            result = subprocess.run(
                [python_exe, "--version"], capture_output=True, text=True
            )
            ver = result.stdout.strip()
            if "3.10" in ver:
                print(f"  .venv already exists with {ver}, reusing it.")
                return python_exe

        print("  Removing existing .venv (wrong Python version)...")
        shutil.rmtree(venv_path, ignore_errors=True)

    # uv venv will auto-download Python 3.10 if not present
    # --seed installs pip/setuptools into the venv (install.py needs pip)
    run(["uv", "venv", "--seed", "--python", PYTHON_VERSION, VENV_DIR], cwd=SCRIPT_DIR)

    python_exe = _get_venv_python(venv_path)
    if not python_exe or not os.path.isfile(python_exe):
        print("*** ERROR: Failed to create virtual environment. ***")
        sys.exit(1)

    result = subprocess.run(
        [python_exe, "--version"], capture_output=True, text=True
    )
    print(f"  Virtual environment created: {result.stdout.strip()}")
    return python_exe


def _get_venv_python(venv_path):
    """Get the Python executable path inside the venv."""
    if platform.system() == "Windows":
        return os.path.join(venv_path, "Scripts", "python.exe")
    else:
        return os.path.join(venv_path, "bin", "python")


def run_install(python_exe):
    """Run install.py using the venv's Python."""
    print("\n[3/3] Running install.py...")
    install_script = os.path.join(SCRIPT_DIR, "install.py")

    # Prepare env for install.py subprocess:
    env = os.environ.copy()
    # 1. Avoid pip cache permission errors (common on Windows when cache dir
    #    is locked or has restrictive ACLs from a previous Python install)
    env["PIP_NO_CACHE_DIR"] = "1"
    # 2. Put venv Scripts/bin on PATH so install.py can find streamlit etc.
    venv_path = os.path.join(SCRIPT_DIR, VENV_DIR)
    if platform.system() == "Windows":
        venv_bin = os.path.join(venv_path, "Scripts")
    else:
        venv_bin = os.path.join(venv_path, "bin")
    env["PATH"] = venv_bin + os.pathsep + env.get("PATH", "")

    run([python_exe, install_script], cwd=SCRIPT_DIR, env=env)


def main():
    print("=" * 60)
    print("  VideoLingo Environment Setup (conda-free)")
    print("=" * 60)
    print(f"\n  Project dir : {SCRIPT_DIR}")
    print(f"  Python ver  : {PYTHON_VERSION}")
    print(f"  Venv dir    : {VENV_DIR}")

    skip_install = "--skip-install" in sys.argv

    install_uv()
    python_exe = create_venv()

    if skip_install:
        print(f"\n  --skip-install: Skipping install.py")
        print(f"\n  To install dependencies manually:")
        print(f"    {python_exe} install.py")
    else:
        run_install(python_exe)

    print("\n" + "=" * 60)
    print("  Setup complete!")
    print("=" * 60)
    print(f"\n  To start VideoLingo:")
    if platform.system() == "Windows":
        print(f"    .venv\\Scripts\\streamlit run st.py")
        print(f"    (or double-click OneKeyStart_uv.bat)")
    else:
        print(f"    .venv/bin/streamlit run st.py")
    print()


if __name__ == "__main__":
    main()
