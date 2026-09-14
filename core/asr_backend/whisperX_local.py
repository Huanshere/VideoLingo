import os
import warnings
import time
import torch
import functools
from pathlib import Path

warnings.filterwarnings("ignore")

# =============================================================================
# Compatibility shim — applied BEFORE importing whisperx
# =============================================================================

# torch.load: default weights_only=False for pyannote checkpoints
# PyTorch >=2.6 changed torch.load default to weights_only=True.
# pyannote checkpoints contain omegaconf objects that fail the safety check.
# Monkey-patch torch.load to default to weights_only=False (matching <2.6
# behavior).  This is safe here because all model files come from trusted
# sources (HuggingFace / pyannote).
_original_torch_load = torch.load
@functools.wraps(_original_torch_load)
def _patched_torch_load(*args, **kwargs):
    if kwargs.get("weights_only") is None:
        kwargs["weights_only"] = False
    return _original_torch_load(*args, **kwargs)
torch.load = _patched_torch_load

# =============================================================================
# Now safe to import whisperx and the rest of the application
# =============================================================================
import whisperx
from whisperx.audio import load_audio as _whisperx_load_audio, SAMPLE_RATE as _WHISPERX_SR
from rich import print as rprint
from core.utils import *
MODEL_DIR = load_key("model_dir")


def _complete_model_directory(path):
    required = ('config.json', 'model.bin', 'tokenizer.json')
    return all((Path(path) / name).is_file() and (Path(path) / name).stat().st_size > 0
               for name in required)


def resolve_whisper_model(model_name, model_dir):
    """Resolve complete local files before allowing any Hub request."""
    from faster_whisper.utils import download_model
    from huggingface_hub.errors import LocalEntryNotFoundError

    explicit = Path(model_name)
    project = Path(model_dir) / model_name
    for directory in (explicit, project):
        if directory.is_dir():
            if not _complete_model_directory(directory):
                raise ValueError(
                    f'Local model directory is incomplete: {directory}. '
                    'Expected non-empty config.json, model.bin and tokenizer.json.'
                )
            rprint(f'[green]Using local Whisper model (no Hub lookup): {directory.resolve()}[/green]')
            return str(directory.resolve())

    # The installed loader owns aliases (large/turbo/distil) and HF cache locations.
    # local_files_only resolves the cached revision without checking the network.
    for cache_dir in (str(model_dir), None):
        try:
            snapshot = download_model(model_name, cache_dir=cache_dir, local_files_only=True)
        except LocalEntryNotFoundError:
            continue
        if _complete_model_directory(snapshot):
            rprint(f'[green]Using cached Whisper model (no Hub lookup): {snapshot}[/green]')
            return snapshot

    rprint('[yellow]No complete Whisper model found locally. Fetching missing files '
           'from the configured HuggingFace endpoint into the global cache.[/yellow]')
    snapshot = download_model(model_name)
    if not _complete_model_directory(snapshot):
        raise RuntimeError('Downloaded Whisper model is incomplete')
    rprint(f'[green]Whisper model files ready: {snapshot}[/green]')
    return snapshot

@except_handler("WhisperX processing error:")
def transcribe_audio(raw_audio_file, vocal_audio_file, start, end):
    WHISPER_LANGUAGE = load_key("whisper.language")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    rprint(f"🚀 Starting WhisperX using device: {device} ...")
    
    if device == "cuda":
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        batch_size = 16 if gpu_mem > 8 else 2
        compute_type = "float16" if torch.cuda.is_bf16_supported() else "int8"
        rprint(f"[cyan]🎮 GPU memory:[/cyan] {gpu_mem:.2f} GB, [cyan]📦 Batch size:[/cyan] {batch_size}, [cyan]⚙️ Compute type:[/cyan] {compute_type}")
    else:
        batch_size = 1
        compute_type = "int8"
        rprint(f"[cyan]📦 Batch size:[/cyan] {batch_size}, [cyan]⚙️ Compute type:[/cyan] {compute_type}")
    rprint(f"[green]▶️ Starting WhisperX for segment {start:.2f}s to {end:.2f}s...[/green]")
    
    if WHISPER_LANGUAGE == 'zh':
        model_name = "Huan69/Belle-whisper-large-v3-zh-punct-fasterwhisper"
        local_model = Path(MODEL_DIR) / "Belle-whisper-large-v3-zh-punct-fasterwhisper"
        if local_model.is_dir():
            model_name = str(local_model.resolve())
    else:
        model_name = load_key("whisper.model")
    model_name = resolve_whisper_model(model_name, MODEL_DIR)

    vad_options = {"vad_onset": 0.500,"vad_offset": 0.363}
    asr_options = {"temperatures": [0],"initial_prompt": "",}
    whisper_language = None if 'auto' in WHISPER_LANGUAGE else WHISPER_LANGUAGE
    load_kwargs = dict(
        device=device,
        compute_type=compute_type,
        language=whisper_language,
        vad_options=vad_options,
        asr_options=asr_options,
        local_files_only=True,
    )
    model = whisperx.load_model(model_name, **load_kwargs)

    def load_audio_segment(audio_file, start, end):
        # Use whisperx's ffmpeg-based loader instead of librosa.load() which
        # deadlocks inside Streamlit's ScriptRunner thread.
        full_audio = _whisperx_load_audio(audio_file, sr=_WHISPERX_SR)
        start_sample = int(start * _WHISPERX_SR)
        end_sample = int(end * _WHISPERX_SR)
        return full_audio[start_sample:end_sample]

    raw_audio_segment = load_audio_segment(raw_audio_file, start, end)
    vocal_audio_segment = load_audio_segment(vocal_audio_file, start, end)
    
    # -------------------------
    # 1. transcribe raw audio
    # -------------------------
    transcribe_start_time = time.time()
    rprint("[bold green]Note: You will see Progress if working correctly ↓[/bold green]")
    result = model.transcribe(raw_audio_segment, batch_size=batch_size, print_progress=True)
    transcribe_time = time.time() - transcribe_start_time
    rprint(f"[cyan]⏱️ time transcribe:[/cyan] {transcribe_time:.2f}s")

    # Free GPU resources
    del model
    torch.cuda.empty_cache()

    # Save language
    detected_language = result['language']
    update_key("whisper.detected_language", detected_language)
    if result['language'] == 'zh' and WHISPER_LANGUAGE != 'zh':
        raise ValueError("Please specify the transcription language as zh and try again!")

    # -------------------------
    # 2. align by vocal audio
    # -------------------------
    align_start_time = time.time()
    # Align timestamps using vocal audio
    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    result = whisperx.align(result["segments"], model_a, metadata, vocal_audio_segment, device, return_char_alignments=False)
    result["language"] = detected_language
    align_time = time.time() - align_start_time
    rprint(f"[cyan]⏱️ time align:[/cyan] {align_time:.2f}s")

    # Free GPU resources again
    torch.cuda.empty_cache()
    del model_a

    # Adjust timestamps
    for segment in result['segments']:
        segment['start'] += start
        segment['end'] += start
        for word in segment['words']:
            if 'start' in word:
                word['start'] += start
            if 'end' in word:
                word['end'] += start
    return result
