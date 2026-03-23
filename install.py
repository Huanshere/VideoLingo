import os, sys
import platform
import subprocess
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

ascii_logo = """
__     ___     _            _     _                    
\ \   / (_) __| | ___  ___ | |   (_)_ __   __ _  ___  
 \ \ / /| |/ _` |/ _ \/ _ \| |   | | '_ \ / _` |/ _ \ 
  \ V / | | (_| |  __/ (_) | |___| | | | | (_| | (_) |
   \_/  |_|\__,_|\___|\___/|_____|_|_| |_|\__, |\___/ 
                                          |___/        
"""

def install_package(*packages):
    subprocess.check_call([sys.executable, "-m", "pip", "install", *packages])

def check_nvidia_gpu():
    install_package("nvidia-ml-py")
    import pynvml
    from translations.translations import translate as t
    initialized = False
    try:
        pynvml.nvmlInit()
        initialized = True
        device_count = pynvml.nvmlDeviceGetCount()
        if device_count > 0:
            print(t("Detected NVIDIA GPU(s)"))
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(handle)
                print(f"GPU {i}: {name}")
            return True
        else:
            print(t("No NVIDIA GPU detected"))
            return False
    except pynvml.NVMLError:
        print(t("No NVIDIA GPU detected or NVIDIA drivers not properly installed"))
        return False
    finally:
        if initialized:
            pynvml.nvmlShutdown()

def check_ffmpeg():
    from rich.console import Console
    from rich.panel import Panel
    from translations.translations import translate as t
    console = Console()

    try:
        # Check if ffmpeg is installed
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        console.print(Panel(t("✅ FFmpeg is already installed"), style="green"))
    except (subprocess.CalledProcessError, FileNotFoundError):
        system = platform.system()
        install_cmd = ""
        
        if system == "Windows":
            install_cmd = "choco install ffmpeg"
            extra_note = t("Install Chocolatey first (https://chocolatey.org/)")
        elif system == "Darwin":
            install_cmd = "brew install ffmpeg"
            extra_note = t("Install Homebrew first (https://brew.sh/)")
        elif system == "Linux":
            install_cmd = "sudo apt install ffmpeg  # Ubuntu/Debian\nsudo yum install ffmpeg  # CentOS/RHEL"
            extra_note = t("Use your distribution's package manager")
        
        console.print(Panel.fit(
            t("❌ FFmpeg not found\n\n") +
            f"{t('🛠️ Install using:')}\n[bold cyan]{install_cmd}[/bold cyan]\n\n" +
            f"{t('💡 Note:')}\n{extra_note}\n\n" +
            f"{t('🔄 After installing FFmpeg, please run this installer again:')}\n[bold cyan]python install.py[/bold cyan]",
            style="red"
        ))
        raise SystemExit(t("FFmpeg is required. Please install it and run the installer again."))

    # Warn if ffmpeg lacks libmp3lame (common with conda-forge builds)
    try:
        result = subprocess.run(['ffmpeg', '-encoders'], capture_output=True, text=True, timeout=10)
        if 'libmp3lame' not in result.stdout:
            console.print(Panel.fit(
                "⚠️ Your ffmpeg does not include [bold]libmp3lame[/bold] (MP3 encoder).\n"
                "This is common with conda-forge ffmpeg builds.\n\n"
                "VideoLingo will fall back to WAV encoding automatically, but for\n"
                "smaller intermediate files, consider installing a full ffmpeg:\n\n"
                "[bold cyan]" + (
                    "winget install Gyan.FFmpeg" if platform.system() == "Windows"
                    else "brew install ffmpeg" if platform.system() == "Darwin"
                    else "sudo apt install ffmpeg"
                ) + "[/bold cyan]",
                style="yellow"
            ))
    except Exception:
        pass

def _detect_cuda_version_from_smi():
    """Detect CUDA version from nvidia-smi output (driver's CUDA capability)."""
    import re
    try:
        result = subprocess.run(
            ["nvidia-smi"], capture_output=True, text=True, timeout=10
        )
        m = re.search(r"CUDA Version:\s*(\d+)\.(\d+)", result.stdout)
        if m:
            return (int(m.group(1)), int(m.group(2)))
    except Exception:
        pass
    return None


def _detect_cuda_index():
    """Detect the CUDA version and return the best PyTorch wheel index URL.
    Falls back to cu126 when detection fails.

    For RTX 50 series (Blackwell architecture, compute capability 10.0+),
    we need PyTorch wheels compiled with CUDA 12.8+ that include sm_100 kernels.

    We prefer nvidia-smi (driver CUDA version) over nvcc (toolkit version) because:
    - Driver version determines what CUDA features the GPU can run at runtime
    - Toolkit version is for compilation, not runtime compatibility
    - Blackwell GPUs need cu129+ wheels even if user has older CUDA toolkit installed
    """
    cuda_version = _detect_cuda_version_from_smi()

    # Map CUDA major.minor to PyTorch wheel index.
    # For CUDA 13.x (RTX 50 series / Blackwell), use cu129 which includes sm_100 kernels.
    INDEX = "https://download.pytorch.org/whl"
    CU_TAGS = [
        ((13, 0), "cu129"),  # CUDA 13.x (Blackwell / RTX 50 series)
        ((12, 9), "cu129"),  # CUDA 12.9+
        ((12, 8), "cu128"),  # CUDA 12.8+
        ((12, 6), "cu126"),  # CUDA 12.6+
    ]

    if cuda_version:
        for min_ver, tag in CU_TAGS:
            if cuda_version >= min_ver:
                return f"{INDEX}/{tag}"

    # Default: cu126 is the broadest CUDA 12 index for PyTorch 2.8
    return f"{INDEX}/cu126"

def main():
    install_package("requests", "rich", "ruamel.yaml", "InquirerPy")
    from rich.console import Console
    from rich.panel import Panel
    from rich.box import DOUBLE
    from InquirerPy import inquirer
    from translations.translations import translate as t
    from translations.translations import DISPLAY_LANGUAGES
    from core.utils.config_utils import load_key, update_key
    from core.utils.decorator import except_handler

    console = Console()
    
    width = max(len(line) for line in ascii_logo.splitlines()) + 4
    welcome_panel = Panel(
        ascii_logo,
        width=width,
        box=DOUBLE,
        title="[bold green]🌏[/bold green]",
        border_style="bright_blue"
    )
    console.print(welcome_panel)
    # Language selection
    current_language = load_key("display_language")
    # Find the display name for current language code
    current_display = next((k for k, v in DISPLAY_LANGUAGES.items() if v == current_language), "🇬🇧 English")
    selected_language = DISPLAY_LANGUAGES[inquirer.select(
        message="Select language / 选择语言 / 選擇語言 / 言語を選択 / Seleccionar idioma / Sélectionner la langue / Выберите язык:",
        choices=list(DISPLAY_LANGUAGES.keys()),
        default=current_display
    ).execute()]
    update_key("display_language", selected_language)

    console.print(Panel.fit(t("🚀 Starting Installation"), style="bold magenta"))

    # Configure mirrors
    # add a check to ask user if they want to configure mirrors
    if inquirer.confirm(
        message=t("Do you need to auto-configure PyPI mirrors? (Recommended if you have difficulty accessing pypi.org)"),
        default=True
    ).execute():
        from core.utils.pypi_autochoose import main as choose_mirror
        choose_mirror()

    # Detect system and GPU
    has_gpu = platform.system() != 'Darwin' and check_nvidia_gpu()

    @except_handler("Failed to install PyTorch", retry=1, delay=5)
    def install_pytorch():
        if has_gpu:
            console.print(Panel(t("🎮 NVIDIA GPU detected, installing CUDA version of PyTorch..."), style="cyan"))
            cuda_index = _detect_cuda_index()
            console.print(f"[cyan]📦 Using PyTorch index:[/cyan] {cuda_index}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "torch==2.8.0", "torchaudio==2.8.0", "--index-url", cuda_index])
        else:
            system_name = "🍎 MacOS" if platform.system() == 'Darwin' else "💻 No NVIDIA GPU"
            console.print(Panel(t(f"{system_name} detected, installing CPU version of PyTorch... Note: it might be slow during whisperX transcription."), style="cyan"))
            subprocess.check_call([sys.executable, "-m", "pip", "install", "torch==2.8.0", "torchaudio==2.8.0"])

    @except_handler("Failed to install project", retry=1, delay=5)
    def install_requirements():
        # Install demucs separately with --no-deps to avoid its outdated
        # torchaudio<2.2 constraint conflicting with whisperx's torchaudio>=2.5.1.
        # demucs works fine with torchaudio 2.6.0 at runtime.
        console.print(Panel(t("Installing demucs (--no-deps to avoid torchaudio conflict)..."), style="cyan"))
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-deps", "demucs[dev]@git+https://github.com/adefossez/demucs"])
        # demucs --no-deps skips its own dependencies; install the ones it
        # actually needs at runtime that aren't already pulled in elsewhere.
        console.print(Panel(t("Installing demucs runtime dependencies..."), style="cyan"))
        subprocess.check_call([sys.executable, "-m", "pip", "install", "dora-search", "openunmix", "lameenc"])

        console.print(Panel(t("Installing project in editable mode using `pip install -e .`"), style="cyan"))
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."], env={**os.environ, "PYTHONIOENCODING": "utf-8"})

    @except_handler("Failed to install Noto fonts")
    def install_noto_font():
        # Detect Linux distribution type
        if os.path.exists('/etc/debian_version'):
            # Debian/Ubuntu systems
            cmd = ['sudo', 'apt-get', 'install', '-y', 'fonts-noto']
            pkg_manager = "apt-get"
        elif os.path.exists('/etc/redhat-release'):
            # RHEL/CentOS/Fedora systems
            cmd = ['sudo', 'yum', 'install', '-y', 'google-noto*']
            pkg_manager = "yum"
        else:
            console.print("Warning: Unrecognized Linux distribution, please install Noto fonts manually", style="yellow")
            return

        subprocess.run(cmd, check=True)
        console.print(f"✅ Successfully installed Noto fonts using {pkg_manager}", style="green")

    if platform.system() == 'Linux':
        install_noto_font()
    
    install_pytorch()
    install_requirements()
    check_ffmpeg()
    
    # First panel with installation complete and startup command
    panel1_text = (
        t("Installation completed") + "\n\n" +
        t("Now I will run this command to start the application:") + "\n" +
        "[bold]streamlit run st.py[/bold]\n" +
        t("Note: First startup may take up to 1 minute")
    )
    console.print(Panel(panel1_text, style="bold green"))

    # Second panel with troubleshooting tips
    panel2_text = (
        t("If the application fails to start:") + "\n" +
        "1. " + t("Check your network connection") + "\n" +
        "2. " + t("Re-run the installer: [bold]python install.py[/bold]")
    )
    console.print(Panel(panel2_text, style="yellow"))

    # start the application
    subprocess.Popen([sys.executable, "-m", "streamlit", "run", "st.py"])

if __name__ == "__main__":
    main()
