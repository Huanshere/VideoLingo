"""Resumable VideoLingo installer and environment checker.

This script is intentionally split from setup_env.py:
- setup_env.py creates/selects the venv.
- installer.py installs packages inside the selected venv.
- OneKeyStart.bat installs on first run, then uses ``--quick-check`` before launch.

The installer is stage-based and safe to rerun. Network-sensitive optional
packages (Demucs, spaCy model downloads) warn instead of breaking the whole
installation.

The default local ASR is Qwen3-ASR + Qwen3-ForcedAligner, installed from
requirements.txt (mlx-audio on Apple Silicon, qwen-asr elsewhere). This installer
only installs Qwen. It does not install WhisperX, prompt for it, or accept a flag
for it. To use WhisperX, follow docs/pages/docs/whisperx-manual.*.md and install
the extra packages yourself. On Apple Silicon, a rerun removes a leftover WhisperX
stack from the default environment (it cannot share huggingface-hub with MLX) and
does not install WhisperX again. Windows and Linux leave a manual WhisperX install
in place.
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
from runtime_libraries import configure_ffmpeg, validate_ffmpeg


ROOT = Path(__file__).resolve().parent
STATE_FILE = Path(sys.prefix) / ".videolingo-install.json"
REQUIREMENTS = ROOT / "requirements.txt"

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
    torch, torchvision = torch_versions()
    h.update(f"torch={torch};torchvision={torchvision}\n".encode())
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
        "qwen-asr": package_version("qwen-asr"),
        "mlx-audio": package_version("mlx-audio"),
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


def apple_silicon() -> bool:
    return platform.system() == "Darwin" and platform.machine() == "arm64"


def intel_mac() -> bool:
    return platform.system() == "Darwin" and platform.machine() == "x86_64"


def torch_versions() -> tuple[str, str]:
    # PyTorch 2.2.x is the last wheel family published for Intel macOS.
    return ("2.2.2", "0.17.2") if intel_mac() else ("2.8.0", "0.23.0")


def qwen_asr_package() -> str:
    """Package providing the default Qwen3-ASR backend on this platform."""
    return "mlx-audio" if apple_silicon() else "qwen-asr"


def unsupported_platform() -> str | None:
    """Explain why the default stack cannot install here, before pip fails on missing wheels."""
    if platform.system() != "Darwin":
        return None
    if intel_mac():
        return None
    if platform.machine() != "arm64":
        return f"Unsupported macOS CPU architecture: {platform.machine()}"
    release = platform.mac_ver()[0]
    try:
        major = int(release.split(".")[0])
    except ValueError:
        return None
    if major < 14:
        return (f"Apple Silicon needs macOS 14 or newer: mlx (used by the default Qwen3-ASR engine) "
                f"only ships macOS 14+ wheels, and this Mac runs macOS {release}.")
    return None


# WhisperX 3.8 pins huggingface-hub<1; mlx-audio needs hub>=1, so on Apple Silicon
# a leftover WhisperX stack cannot stay in the default environment. These are the
# packages that only the WhisperX stack brings in (none is in the resolved default
# requirements); leaving pyannote-audio without torchcodec breaks `pip check`.
# This is conflict cleanup, not an install option. Windows and Linux never uninstall them.
# Generic libraries it also pulled in (matplotlib, lightning, ...) stay installed.
WHISPERX_ONLY_PACKAGES = (
    "whisperx", "torchcodec", "faster-whisper", "ctranslate2",
    "pyannote-audio", "pyannote-core", "pyannote-database", "pyannote-metrics",
    "pyannote-pipeline", "pyannoteai-sdk",
)


def canonical_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def required_by_other_packages(names: list[str]) -> set[str]:
    """Candidates reachable from other installed packages, including transitive dependencies."""
    from packaging.requirements import InvalidRequirement, Requirement
    candidates = {canonical_name(name) for name in names}
    dependencies: dict[str, set[str]] = {}
    for dist in metadata.distributions():
        owner = canonical_name(dist.metadata["Name"] or "")
        # The project's own (possibly stale) metadata is re-registered from requirements.txt.
        if owner == "videolingo":
            continue
        required = dependencies.setdefault(owner, set())
        for raw in dist.requires or []:
            try:
                req = Requirement(raw)
            except InvalidRequirement:
                continue
            if req.marker and not req.marker.evaluate({"extra": ""}):
                continue
            required.add(canonical_name(req.name))
    pending = list(dependencies.keys() - candidates)
    visited: set[str] = set()
    while pending:
        name = pending.pop()
        if name in visited:
            continue
        visited.add(name)
        pending.extend(dependencies.get(name, set()) - visited)
    return candidates & visited


def remove_whisperx_for_mlx() -> None:
    if not apple_silicon():
        return
    installed = [name for name in WHISPERX_ONLY_PACKAGES if package_version(name) is not None]
    if not installed:
        return
    kept = required_by_other_packages(installed)
    removable = [name for name in installed if name not in kept]
    print("  WhisperX cannot share an environment with the default MLX ASR on Apple Silicon "
          "(huggingface-hub <1 vs >=1). Removing the WhisperX stack: " + ", ".join(removable))
    if kept:
        print("  Keeping (required by other installed packages): " + ", ".join(sorted(kept)))
    print("  To keep using WhisperX on this Mac, create a separate environment and follow "
          "docs/pages/docs/whisperx-manual.en-US.md. This installer will not install WhisperX again.")
    if removable:
        run([sys.executable, "-m", "pip", "uninstall", "-y", *removable])


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
        match = re.search(r"CUDA(?: UMD)? Version:\s*(\d+)\.(\d+)", result.stdout)
        if match:
            return int(match.group(1)), int(match.group(2))
    except Exception:
        pass
    return None


def detect_torch_index() -> str:
    cuda_version = detect_cuda_version_from_smi()
    tags = [
        # PyTorch 2.8 wheels exist for CUDA 12.6/12.8; CUDA 13 drivers run them too.
        ((12, 8), "cu128"),
        ((12, 6), "cu126"),
    ]
    if cuda_version:
        for minimum, tag in tags:
            if cuda_version >= minimum:
                return f"{TORCH_INDEX}/{tag}"
    return f"{TORCH_INDEX}/cu126"


def install_bootstrap() -> None:
    print("\n[1/6] Bootstrap installer packages")
    missing = [pkg for pkg in BOOTSTRAP_PACKAGES if package_version(pkg) is None]
    if missing:
        pip_install(missing)
    else:
        print("  Bootstrap packages already installed.")


def maybe_configure_mirror(auto_mirror: bool) -> None:
    if not auto_mirror:
        return
    print("\n[2/6] Configure PyPI mirror")
    try:
        from core.utils.pypi_autochoose import main as choose_mirror

        choose_mirror()
    except Exception as exc:
        print(f"  Warning: mirror auto-config failed: {exc}")


def install_torch(force: bool = False, backend: str = "auto") -> None:
    print("\n[3/6] Install PyTorch / torchaudio")
    torch_version, vision_version = torch_versions()
    gpu = (platform.system() != "Darwin" and detect_nvidia_gpu()) if backend == "auto" else backend != "cpu"
    builds = {(package_version(name) or "").partition("+")[2] or "cpu" for name in ("torch", "torchaudio", "torchvision")}
    expected = {backend} if backend != "auto" else ({"cu126", "cu128"} if gpu else {"cpu"})
    gpu_build = len(builds) == 1 and builds <= expected
    if not force and gpu_build and package_ok("torch", torch_version) and package_ok("torchaudio", torch_version) and package_ok("torchvision", vision_version):
        print(f"  torch {package_version('torch')} and torchaudio {package_version('torchaudio')} already installed.")
        return
    packages = [f"torch=={torch_version}", f"torchaudio=={torch_version}", f"torchvision=={vision_version}"]
    if gpu:
        index = detect_torch_index() if backend == "auto" else f"{TORCH_INDEX}/{backend}"
        print(f"  Using CUDA PyTorch index: {index}")
        pip_install(packages, retries=3, extra_args=["--index-url", index, "--force-reinstall"])
    else:
        print("  No NVIDIA GPU detected. Installing CPU PyTorch wheels.")
        extra = ["--index-url", f"{TORCH_INDEX}/cpu"] if platform.system() != "Darwin" else []
        pip_install(packages, retries=3, extra_args=[*extra, "--force-reinstall"])


def install_base_requirements(force: bool = False, upgrade: bool = False) -> None:
    print("\n[4/6] Install base requirements")
    remove_whisperx_for_mlx()
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
        if package_version("videolingo") is not None:
            # The installed project metadata still lists the previous requirements
            # (e.g. whisperx, transformers<5); pip would print a resolver ERROR against
            # it while syncing. Re-register it first (--no-deps skips pip's conflict check).
            refresh_project_metadata()
    pip_install(read_base_requirements(), retries=3, extra_args=["--upgrade"])


def install_spacy(force: bool = False) -> None:
    print("\n[5/6] Install spaCy")
    if not force and package_ok("spacy", "3.8."):
        print(f"  spacy {package_version('spacy')} already installed.")
        return
    # Keep this flexible. Exact spaCy patch releases can disappear for a Python
    # minor version, which made plain `pip install -r requirements.txt` brittle.
    pip_install(["spacy>=3.8.7,<3.9"], retries=3)


def install_demucs(force: bool = False, require: bool = False) -> None:
    print("\n[6/6] Install Demucs (optional)")
    from packaging.version import Version
    if not force and package_version("demucs") is not None and Version("4.1.0") <= Version(package_version("demucs")) < Version("5") and import_ok("demucs.api"):
        print(f"  demucs {package_version('demucs')} already installed.")
        return
    if intel_mac():
        message = "Demucs is not installed automatically on Intel macOS: its sphn dependency has no x86_64 wheel. Vocal separation will be unavailable."
        if require:
            raise RuntimeError(message)
        print(f"  Warning: {message}")
        return
    # Maintained Demucs separates inference and training dependencies. No git
    # snapshot, no-deps installation, or torchaudio<2.2 workaround is needed.
    ok = soft_pip_install([DEMUCS_REQUIREMENT], retries=2, extra_args=["--upgrade"])
    if require and not ok:
        raise RuntimeError("Demucs installation failed")


def refresh_project_metadata() -> bool:
    return soft_pip_install(["-e", str(ROOT)], retries=1, extra_args=["--no-deps"])


def install_project_metadata() -> None:
    print("\n[post] Register project metadata (no dependency resolution)")
    refresh_project_metadata()


def check_ffmpeg() -> bool:
    print("\n[post] Prepare FFmpeg and ffprobe automatically")
    try:
        configure_ffmpeg(download=True, required=True)
        print("  " + validate_ffmpeg())
    except Exception as exc:
        print(f"  ERROR: Automatic FFmpeg setup failed: {exc}. Check your connection and rerun installer.py.")
        return False
    return True


def whisperx_selected() -> bool:
    """A leftover optional package must not block the default Qwen install."""
    from ruamel.yaml import YAML
    config = YAML(typ="safe").load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    whisper = config.get("whisper", {})
    return whisper.get("runtime", "local") == "local" and whisper.get("backend", "qwen") == "whisperx"


def noto_cjk_font_available() -> bool:
    if platform.system() != "Linux" or not shutil.which("fc-match"):
        return False
    result = subprocess.run(
        ["fc-match", "Noto Sans CJK SC"],
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


def health_check(quiet: bool = False, require_demucs: bool = False, check_state: bool = True,
                 torch_backend: str = "auto", quick: bool = False) -> int:
    errors: list[str] = []
    warnings: list[str] = []
    if sys.version_info[:2] != (3, 12):
        errors.append("VideoLingo uses Python 3.12; rerun setup_env.py")
    torch_version, vision_version = torch_versions()
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
        "torch": torch_version,
        "torchaudio": torch_version,
        "torchvision": vision_version,
        "spacy": "3.8.",
        qwen_asr_package(): None,
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
    try:
        configure_ffmpeg(required=True)
        if not errors and not quick:
            validate_ffmpeg()
    except (RuntimeError, OSError, subprocess.SubprocessError) as exc:
        errors.append(f"FFmpeg runtime check failed: {exc}")
    builds = {(package_version(name) or "").partition("+")[2] or "cpu" for name in ("torch", "torchaudio", "torchvision")}
    if len(builds) != 1:
        errors.append("torch, torchaudio and torchvision must use the same CPU/CUDA build")
    if torch_backend == "auto":
        if not quick and platform.system() != "Darwin" and detect_nvidia_gpu() and not builds <= {"cu126", "cu128"}:
            errors.append("NVIDIA GPU detected: auto accepts only cu126/cu128 PyTorch builds; "
                          f"detected builds: {', '.join(sorted(builds))}. Rerun installer.py")
    elif builds != {torch_backend}:
        errors.append(f"PyTorch build does not match requested {torch_backend}")
    if apple_silicon() and package_version("whisperx") is not None:
        errors.append("whisperx is installed next to the MLX ASR stack (huggingface-hub <1 vs >=1); "
                      "rerun installer.py to remove it and use a separate environment for WhisperX. "
                      "The installer will not install WhisperX again; see "
                      "docs/pages/docs/whisperx-manual.en-US.md")
    # Our WhisperX path uses CLI decoding and passes waveforms to pyannote.
    # TorchCodec's optional filename decoder need not load for this to work.
    if not errors and not quick and whisperx_selected():
        try:
            probe = subprocess.run(
                [sys.executable, "-c", "from runtime_libraries import check_whisperx_runtime; "
                 "check_whisperx_runtime()"],
                cwd=ROOT, capture_output=True, text=True, timeout=60,
            )
            if probe.returncode:
                errors.append("WhisperX audio runtime check failed. Check the optional packages and "
                              "managed FFmpeg installation; see docs/pages/docs/whisperx-manual.en-US.md.\n" + probe.stderr)
        except (OSError, subprocess.TimeoutExpired) as exc:
            errors.append(f"WhisperX audio runtime check failed: {exc}")
    if not quiet:
        print("\nEnvironment check")
        for package in ["streamlit", "torch", "torchaudio", "spacy", qwen_asr_package(), "demucs"]:
            print(f"  {package}: {package_version(package) or 'missing'}")
        # WhisperX is not part of this install. Mention it only when a manual install is present.
        if package_version("whisperx"):
            print(f"  whisperx: {package_version('whisperx')} (not part of this install)")
        for warning in warnings:
            print(f"  WARN: {warning}")
        for error in errors:
            print(f"  ERROR: {error}")
    return 1 if errors else 0


def print_asr_summary() -> None:
    """Describe local Qwen settings without loading models or changing configuration."""
    from ruamel.yaml import YAML
    from ruamel.yaml.error import YAMLError

    try:
        config = YAML(typ="safe").load((ROOT / "config.yaml").read_text(encoding="utf-8"))
        config = config if isinstance(config, dict) else {}
    except (OSError, ValueError, YAMLError):
        config = {}
    whisper = config.get("whisper") or {}
    size = str(whisper.get("qwen_model", "1.7b")).lower() if isinstance(whisper, dict) else "1.7b"
    model = f"Qwen3-ASR-{size.upper()}" if size in ("0.6b", "1.7b") else "Qwen3-ASR-1.7B"
    device, precision, note = "Device information unavailable", None, None
    try:
        if apple_silicon():
            device, precision = "Apple Silicon / MLX", "8-bit"
        else:
            import torch
            if torch.cuda.is_available():
                properties = torch.cuda.get_device_properties(0)
                memory = properties.total_memory / (1024 ** 3)
                device = f"{properties.name} ({memory:.1f} GiB)"
                precision = "BF16" if torch.cuda.is_bf16_supported() else "FP16"
                if round(memory) < 8:
                    note = "For limited GPU memory, Qwen3-ASR-0.6B is available in the model settings."
            else:
                device, precision = "CPU", "FP32"
                note = "CPU recognition is slow. Qwen3-ASR-0.6B is available in the model settings."
    except (ImportError, RuntimeError, OSError):
        pass  # An informational hardware probe must not fail an otherwise healthy install.

    print("\nLocal ASR")
    print(f"  Device: {device}")
    print(f"  Model: {model}" + (f" ({precision})" if precision else ""))
    print("  Aligner: Qwen3-ForcedAligner-0.6B")
    if note:
        print("  " + note)



def launch_streamlit() -> int:
    env = os.environ.copy()
    env["PYTHONWARNINGS"] = "ignore"
    return subprocess.run([sys.executable, "-m", "streamlit", "run", "st.py"], cwd=ROOT, env=env).returncode


def install_all(args: argparse.Namespace) -> int:
    if sys.version_info[:2] != (3, 12):
        print("ERROR: VideoLingo uses Python 3.12. Run setup_env.py first.")
        return 1
    reason = unsupported_platform()
    if reason:
        print(f"ERROR: {reason}")
        return 1
    if platform.system() == "Darwin" and args.torch_backend not in ("auto", "cpu"):
        print("ERROR: macOS uses CPU or MLX; CUDA PyTorch builds are not available.")
        return 1
    install_bootstrap()
    maybe_configure_mirror(args.auto_mirror)
    install_torch(force=args.force, backend=args.torch_backend)
    install_base_requirements(force=args.force, upgrade=args.upgrade)
    install_spacy(force=args.force)
    if not args.skip_demucs:
        install_demucs(force=args.force or args.upgrade, require=args.require_demucs)
    install_project_metadata()
    install_linux_noto_fonts()
    ffmpeg_ok = check_ffmpeg()
    status = health_check(require_demucs=args.require_demucs, check_state=False,
                          torch_backend=args.torch_backend)
    if not ffmpeg_ok or status != 0:
        return 1
    save_state()
    print_asr_summary()
    if args.launch:
        return launch_streamlit()
    print("\nInstall complete. Start with OneKeyStart.bat or: python -m streamlit run st.py")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install or check VideoLingo dependencies")
    parser.add_argument("--check", action="store_true", help="check environment health only")
    parser.add_argument("--quick-check", action="store_true",
                        help="check installed package versions, install state and FFmpeg files without runtime probes")
    parser.add_argument("--torch-backend", choices=("auto", "cpu", "cu126", "cu128"), default="auto",
                        help="auto-detect on hosts; select explicitly for GPU-less image builds")
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
    if args.quick_check:
        return health_check(quiet=args.quiet, require_demucs=args.require_demucs,
                            torch_backend=args.torch_backend, quick=True)
    if args.check:
        return health_check(quiet=args.quiet, require_demucs=args.require_demucs, torch_backend=args.torch_backend)
    return install_all(args)


if __name__ == "__main__":
    raise SystemExit(main())
