"""Resumable VideoLingo installer and environment checker.

This script is intentionally split from setup_env.py:
- setup_env.py creates/selects the venv.
- installer.py installs packages inside the selected venv.
- OneKeyStart.bat starts the app and can call ``installer.py --check``.

The installer is stage-based and safe to rerun. Network-sensitive optional
packages (Demucs, spaCy model downloads) warn instead of breaking the whole
installation.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata as metadata
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
STATE_FILE = Path(sys.prefix) / ".videolingo-install.json"
REQUIREMENTS = ROOT / "requirements.txt"

TORCH_VERSION = "2.8.0"
TORCH_INDEX = "https://download.pytorch.org/whl"
BOOTSTRAP_PACKAGES = ["requests", "rich", "ruamel.yaml", "InquirerPy", "packaging"]
FILTERED_REQUIREMENTS = {"torch", "torchaudio", "torchvision"}
DEMUCS_REQUIREMENT = "demucs>=4.1.0,<5"


def run(cmd: list[str], retries: int = 0, env: dict[str, str] | None = None) -> None:
    for attempt in range(retries + 1):
        print("  > " + " ".join(str(x) for x in cmd), flush=True)
        proc = subprocess.run(cmd, cwd=ROOT, env=env)
        if proc.returncode == 0:
            return
        if attempt < retries:
            delay = min(20, 3 * (attempt + 1))
            print(f"  Command failed, retrying in {delay}s ({attempt + 1}/{retries})...")
            time.sleep(delay)
    raise subprocess.CalledProcessError(proc.returncode, cmd)


def pip_install(packages: list[str], retries: int = 2, extra_args: list[str] | None = None) -> None:
    if not packages:
        return
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "--prefer-binary",
        "--retries",
        "5",
        "--timeout",
        "120",
    ]
    if extra_args:
        cmd.extend(extra_args)
    cmd.extend(packages)
    env = os.environ.copy()
    env.setdefault("PIP_NO_INPUT", "1")
    run(cmd, retries=retries, env=env)


def soft_pip_install(packages: list[str], retries: int = 1, extra_args: list[str] | None = None) -> bool:
    try:
        pip_install(packages, retries=retries, extra_args=extra_args)
        return True
    except Exception as exc:
        print(f"  Warning: optional install failed: {exc}")
        return False


def package_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def package_ok(name: str, prefix: str | None = None) -> bool:
    version = package_version(name)
    if version is None:
        return False
    return prefix is None or version.split("+")[0].startswith(prefix)


def import_ok(module: str) -> bool:
    try:
        importlib.import_module(module)
        return True
    except Exception:
        return False


def requirements_hash() -> str:
    h = hashlib.sha256()
    h.update(REQUIREMENTS.read_bytes())
    h.update(f"torch={TORCH_VERSION}\n".encode())
    h.update(DEMUCS_REQUIREMENT.encode())
    return h.hexdigest()


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state() -> None:
    data = {
        "requirements_hash": requirements_hash(),
        "python": sys.version.split()[0],
        "torch": package_version("torch"),
        "torchaudio": package_version("torchaudio"),
        "spacy": package_version("spacy"),
        "whisperx": package_version("whisperx"),
        "demucs": package_version("demucs"),
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    STATE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def requirement_name(line: str) -> str | None:
    line = line.strip()
    if not line or line.startswith("#") or line.startswith("-"):
        return None
    line = line.split(";", 1)[0].strip()
    name = re.split(r"\s*(?:==|>=|<=|~=|!=|>|<|\[)", line, maxsplit=1)[0]
    return name.strip().lower().replace("_", "-") or None


def read_base_requirements() -> list[str]:
    reqs: list[str] = []
    for raw in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        name = requirement_name(raw)
        if not name or name in FILTERED_REQUIREMENTS:
            continue
        reqs.append(raw.strip())
    return reqs


def detect_nvidia_gpu() -> bool:
    if platform.system() == "Darwin":
        return False
    try:
        result = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except Exception:
        return False


def detect_cuda_version_from_smi() -> tuple[int, int] | None:
    try:
        result = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=10)
        match = re.search(r"CUDA Version:\s*(\d+)\.(\d+)", result.stdout)
        if match:
            return int(match.group(1)), int(match.group(2))
    except Exception:
        pass
    return None


def detect_torch_index() -> str:
    cuda_version = detect_cuda_version_from_smi()
    tags = [
        # CTranslate2 currently requires CUDA 12 cuBLAS, including on CUDA 13 drivers.
        ((12, 8), "cu128"),
        ((12, 6), "cu126"),
    ]
    if cuda_version:
        for minimum, tag in tags:
            if cuda_version >= minimum:
                return f"{TORCH_INDEX}/{tag}"
    return f"{TORCH_INDEX}/cu126"


def install_bootstrap() -> None:
    print("\n[1/7] Bootstrap installer packages")
    missing = [pkg for pkg in BOOTSTRAP_PACKAGES if package_version(pkg) is None]
    if missing:
        pip_install(missing)
    else:
        print("  Bootstrap packages already installed.")


def maybe_configure_mirror(auto_mirror: bool) -> None:
    if not auto_mirror:
        return
    print("\n[2/7] Configure PyPI mirror")
    try:
        from core.utils.pypi_autochoose import main as choose_mirror

        choose_mirror()
    except Exception as exc:
        print(f"  Warning: mirror auto-config failed: {exc}")


def install_torch(force: bool = False) -> None:
    print("\n[3/7] Install PyTorch / torchaudio")
    gpu = detect_nvidia_gpu()
    gpu_build = not gpu or all("+cu12" in (package_version(name) or "") for name in ("torch", "torchaudio", "torchvision"))
    if not force and gpu_build and package_ok("torch", TORCH_VERSION) and package_ok("torchaudio", TORCH_VERSION) and package_ok("torchvision", "0.23.0"):
        print(f"  torch {package_version('torch')} and torchaudio {package_version('torchaudio')} already installed.")
        return
    packages = [f"torch=={TORCH_VERSION}", f"torchaudio=={TORCH_VERSION}", "torchvision==0.23.0"]
    if gpu:
        index = detect_torch_index()
        print(f"  NVIDIA GPU detected. Using PyTorch index: {index}")
        pip_install(packages, retries=3, extra_args=["--index-url", index, "--force-reinstall"])
    else:
        print("  No NVIDIA GPU detected. Installing CPU PyTorch wheels.")
        extra = ["--index-url", f"{TORCH_INDEX}/cpu"] if platform.system() != "Darwin" else []
        pip_install(packages, retries=3, extra_args=extra)


def install_base_requirements(force: bool = False, upgrade: bool = False) -> None:
    print("\n[4/7] Install base requirements")
    state = load_state()
    current_hash = requirements_hash()
    previous_hash = state.get("requirements_hash")
    if not force and not upgrade and previous_hash == current_hash and health_check(quiet=True, require_demucs=False, check_state=False) == 0:
        print("  Environment already matches requirements hash; skipping base install.")
        return
    if not force and not upgrade and previous_hash is None and health_check(quiet=True, require_demucs=False, check_state=False) == 0:
        print("  Packages are already healthy; writing fresh install state later.")
        return
    if previous_hash and previous_hash != current_hash:
        print("  requirements.txt changed; syncing base requirements.")
    pip_install(read_base_requirements(), retries=3, extra_args=["--upgrade"])


def install_spacy(force: bool = False) -> None:
    print("\n[5/7] Install spaCy")
    if not force and package_ok("spacy", "3.8."):
        print(f"  spacy {package_version('spacy')} already installed.")
        return
    # Keep this flexible. Exact spaCy patch releases can disappear for a Python
    # minor version, which made plain `pip install -r requirements.txt` brittle.
    pip_install(["spacy>=3.8.7,<3.9"], retries=3)


def install_whisperx(force: bool = False) -> None:
    print("\n[6/7] Install WhisperX")
    if not force and package_version("whisperx") is not None:
        print(f"  whisperx {package_version('whisperx')} already installed.")
        return
    pip_install(["whisperx>=3.8.6,<3.9"], retries=3)


def install_demucs(force: bool = False, require: bool = False) -> None:
    print("\n[7/7] Install Demucs (optional)")
    from packaging.version import Version
    if not force and package_version("demucs") is not None and Version("4.1.0") <= Version(package_version("demucs")) < Version("5") and import_ok("demucs.api"):
        print(f"  demucs {package_version('demucs')} already installed.")
        return
    # Maintained Demucs separates inference and training dependencies. No git
    # snapshot, no-deps installation, or torchaudio<2.2 workaround is needed.
    ok = soft_pip_install([DEMUCS_REQUIREMENT], retries=2, extra_args=["--upgrade"])
    if require and not ok:
        raise RuntimeError("Demucs installation failed")


def install_project_metadata() -> None:
    print("\n[post] Register project metadata (no dependency resolution)")
    soft_pip_install(["-e", str(ROOT)], retries=1, extra_args=["--no-deps"])


def check_ffmpeg() -> bool:
    if not shutil.which("ffmpeg"):
        print("  ERROR: ffmpeg not found in PATH.")
        if platform.system() == "Windows":
            print("  Install with: winget install Gyan.FFmpeg")
        elif platform.system() == "Darwin":
            print("  Install with: brew install ffmpeg")
        else:
            print("  Install with your distribution package manager, e.g. sudo apt install ffmpeg")
        return False
    return True


def noto_cjk_font_available() -> bool:
    if platform.system() != "Linux" or not shutil.which("fc-match"):
        return False
    result = subprocess.run(
        ["fc-match", "NotoSansCJK-Regular"],
        capture_output=True,
        text=True,
    )
    output = f"{result.stdout} {result.stderr}".lower()
    return result.returncode == 0 and "noto" in output and "cjk" in output


def _privileged_command(cmd: list[str]) -> list[str] | None:
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        return cmd
    if shutil.which("sudo"):
        return ["sudo", *cmd]
    return None


def install_linux_noto_fonts() -> None:
    if platform.system() != "Linux":
        return
    print("\n[post] Check Linux Noto CJK fonts")
    if noto_cjk_font_available():
        print("  Noto CJK fonts already installed.")
        return

    if os.path.exists("/etc/debian_version"):
        cmd = ["apt-get", "install", "-y", "fonts-noto-cjk"]
    elif shutil.which("dnf"):
        cmd = ["dnf", "install", "-y", "google-noto-sans-cjk-fonts"]
    elif shutil.which("yum"):
        cmd = ["yum", "install", "-y", "google-noto-sans-cjk-fonts"]
    elif shutil.which("pacman"):
        cmd = ["pacman", "-S", "--noconfirm", "noto-fonts-cjk"]
    else:
        print("  Warning: unsupported Linux distribution; please install Noto CJK fonts manually.")
        return

    cmd = _privileged_command(cmd)
    if cmd is None:
        print("  Warning: sudo not found; please install Noto CJK fonts manually.")
        return

    try:
        run(cmd)
        if shutil.which("fc-cache"):
            subprocess.run(["fc-cache", "-f"], check=False)
        print("  Noto CJK fonts installed.")
    except Exception as exc:
        print(f"  Warning: failed to install Noto CJK fonts automatically: {exc}")


def health_check(quiet: bool = False, require_demucs: bool = False, check_state: bool = True) -> int:
    errors: list[str] = []
    warnings: list[str] = []
    if not (3, 10) <= sys.version_info[:2] < (3, 14):
        errors.append("WhisperX requires Python >=3.10,<3.14; use setup_env.py")
    try:
        from packaging.requirements import Requirement
        for raw in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
            if not requirement_name(raw):
                continue
            req = Requirement(raw)
            if req.marker and not req.marker.evaluate():
                continue
            installed = package_version(req.name)
            if installed is None or not req.specifier.contains(installed):
                errors.append(f"unsatisfied requirement: {req} (installed: {installed})")
    except ImportError:
        errors.append("missing package: packaging")
    state = load_state()
    if check_state:
        if state.get("requirements_hash") and state.get("requirements_hash") != requirements_hash():
            errors.append("requirements changed since the last install; rerun installer.py")
        elif not state.get("requirements_hash"):
            errors.append("install state file is missing; rerun installer.py once to enable change detection")
    required = {
        "streamlit": None,
        "openai": None,
        "pandas": None,
        "torch": TORCH_VERSION,
        "torchaudio": TORCH_VERSION,
        "spacy": "3.8.",
        "whisperx": None,
    }
    for package, prefix in required.items():
        version = package_version(package)
        if version is None:
            errors.append(f"missing package: {package}")
        elif prefix and not version.split("+")[0].startswith(prefix):
            errors.append(f"{package} version {version} does not match expected {prefix}*")
    if require_demucs and package_version("demucs") is None:
        errors.append("missing optional package required by flag: demucs")
    elif package_version("demucs") is None:
        warnings.append("demucs is not installed; vocal separation will be unavailable")
    if platform.system() == "Linux" and not noto_cjk_font_available():
        warnings.append("Noto CJK fonts are not installed; CJK subtitle burn-in may fail")
    if not shutil.which("ffmpeg"):
        errors.append("ffmpeg not found in PATH")
    if detect_nvidia_gpu() and not all("+cu12" in (package_version(name) or "") for name in ("torch", "torchaudio", "torchvision")):
        errors.append("NVIDIA GPU detected but the matched CUDA 12 PyTorch wheels are missing; rerun installer.py")
    if not quiet:
        print("\nEnvironment check")
        for package in ["streamlit", "torch", "torchaudio", "spacy", "whisperx", "demucs"]:
            print(f"  {package}: {package_version(package) or 'missing'}")
        for warning in warnings:
            print(f"  WARN: {warning}")
        for error in errors:
            print(f"  ERROR: {error}")
    return 1 if errors else 0


def launch_streamlit() -> int:
    env = os.environ.copy()
    env["PYTHONWARNINGS"] = "ignore"
    return subprocess.run([sys.executable, "-m", "streamlit", "run", "st.py"], cwd=ROOT, env=env).returncode


def install_all(args: argparse.Namespace) -> int:
    if not (3, 10) <= sys.version_info[:2] < (3, 14):
        print("ERROR: WhisperX requires Python >=3.10,<3.14. Run setup_env.py first.")
        return 1
    install_bootstrap()
    maybe_configure_mirror(args.auto_mirror)
    install_torch(force=args.force)
    install_base_requirements(force=args.force, upgrade=args.upgrade)
    install_spacy(force=args.force)
    install_whisperx(force=args.force)
    if not args.skip_demucs:
        install_demucs(force=args.force or args.upgrade, require=args.require_demucs)
    install_project_metadata()
    install_linux_noto_fonts()
    ffmpeg_ok = check_ffmpeg()
    save_state()
    status = health_check(require_demucs=args.require_demucs)
    if not ffmpeg_ok or status != 0:
        return 1
    if args.launch:
        return launch_streamlit()
    print("\nInstall complete. Start with OneKeyStart.bat or: python -m streamlit run st.py")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install or check VideoLingo dependencies")
    parser.add_argument("--check", action="store_true", help="check environment health only")
    parser.add_argument("--quiet", action="store_true", help="quiet check output")
    parser.add_argument("--force", action="store_true", help="force reinstall staged packages")
    parser.add_argument("--upgrade", action="store_true", help="refresh dependencies within requirements.txt compatibility bounds")
    parser.add_argument("--auto-mirror", action="store_true", help="auto-select and configure a PyPI mirror")
    parser.add_argument("--skip-demucs", action="store_true", help="skip optional Demucs install")
    parser.add_argument("--require-demucs", action="store_true", help="fail if Demucs cannot be installed")
    parser.add_argument("--launch", action="store_true", help="launch Streamlit after a successful install")
    parser.add_argument("--yes", action="store_true", help="accepted for non-interactive wrappers")
    parser.add_argument("--no-launch", action="store_true", help="compatibility alias; launching is opt-in")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.no_launch:
        args.launch = False
    if args.check:
        return health_check(quiet=args.quiet, require_demucs=args.require_demucs)
    return install_all(args)


if __name__ == "__main__":
    raise SystemExit(main())
