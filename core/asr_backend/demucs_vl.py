import os
import subprocess
import tempfile
from pathlib import Path
import torch
from rich.console import Console
from rich import print as rprint
from demucs.pretrained import get_model
from demucs.audio import AudioFile, save_audio
from torch.cuda import is_available as is_cuda_available
from typing import Optional
from demucs.api import Separator
from demucs.apply import BagOfModels
import gc
from core.utils.models import *
from core.asr_backend.audio_preprocess import _ffmpeg_has_encoder

class PreloadedSeparator(Separator):
    def __init__(self, model: BagOfModels, shifts: int = 1, overlap: float = 0.25,
                 split: bool = True, segment: Optional[int] = None, jobs: int = 0):
        self._model, self._audio_channels, self._samplerate = model, model.audio_channels, model.samplerate
        device = "cuda" if is_cuda_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        self.update_parameter(device=device, shifts=shifts, overlap=overlap, split=split,
                            segment=segment, jobs=jobs, progress=True, callback=None, callback_arg=None)

def save_stem(wav, path, samplerate, bitrate="128k"):
    """Write a stem as MP3 through FFmpeg's libmp3lame.

    demucs.audio.save_audio encodes with lameenc, which writes no LAME/Xing header, so
    decoders cannot trim the encoder delay and the stem plays ~25 ms late. FFmpeg's
    header lets FFmpeg, pydub and soundfile decode it sample-aligned with raw.mp3.
    Without libmp3lame, fall back to PCM WAV content under the same name (as raw.mp3 does).
    """
    with tempfile.TemporaryDirectory() as tmp:
        pcm = Path(tmp) / "stem.wav"
        save_audio(wav, pcm, samplerate=samplerate, clip="rescale", bits_per_sample=16)
        if _ffmpeg_has_encoder("libmp3lame"):
            codec = ["-c:a", "libmp3lame", "-b:a", bitrate]
        else:
            codec = ["-c:a", "pcm_s16le", "-f", "wav"]
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(pcm), *codec, str(path)],
                       check=True, capture_output=True)

def demucs_audio():
    if os.path.exists(_VOCAL_AUDIO_FILE) and os.path.exists(_BACKGROUND_AUDIO_FILE):
        rprint(f"[yellow]⚠️ {_VOCAL_AUDIO_FILE} and {_BACKGROUND_AUDIO_FILE} already exist, skip Demucs processing.[/yellow]")
        return
    
    console = Console()
    os.makedirs(_AUDIO_DIR, exist_ok=True)
    
    console.print("🤖 Loading <htdemucs> model...")
    model = get_model('htdemucs')
    separator = PreloadedSeparator(model=model, shifts=1, overlap=0.25)
    
    console.print("🎵 Separating audio...")
    # Decode with FFmpeg, which trims the MP3 encoder delay of raw.mp3. Demucs'
    # separate_audio_file() reads with sphn first, which keeps that delay and made
    # the stems ~35 ms late relative to raw.mp3 (32 kHz LAME priming).
    wav = AudioFile(_RAW_AUDIO_FILE).read(streams=0, samplerate=model.samplerate,
                                          channels=model.audio_channels)
    _, outputs = separator.separate_tensor(wav, model.samplerate)
    
    console.print("🎤 Saving vocals track...")
    save_stem(outputs['vocals'].cpu(), _VOCAL_AUDIO_FILE, model.samplerate)
    
    console.print("🎹 Saving background music...")
    background = sum(audio for source, audio in outputs.items() if source != 'vocals')
    save_stem(background.cpu(), _BACKGROUND_AUDIO_FILE, model.samplerate)
    
    # Clean up memory
    del outputs, background, model, separator
    gc.collect()
    
    console.print("[green]✨ Audio separation completed![/green]")

if __name__ == "__main__":
    demucs_audio()
