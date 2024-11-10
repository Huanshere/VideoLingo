import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
import torch
from rich.console import Console
from demucs.pretrained import get_model
from demucs.audio import save_audio
from torch.cuda import is_available as is_cuda_available
from typing import Optional
from demucs.api import Separator
from demucs.apply import BagOfModels

class PreloadedSeparator(Separator):
    def __init__(
        self,
        model: BagOfModels,
        shifts: int = 1,
        overlap: float = 0.25,
        split: bool = True,
        segment: Optional[int] = None,
        jobs: int = 0,
    ):
        self._model = model
        self._audio_channels = model.audio_channels
        self._samplerate = model.samplerate

        self.update_parameter(
            device="cuda" if is_cuda_available() else "mps" if torch.backends.mps.is_available() else "cpu",
            shifts=shifts,
            overlap=overlap,
            split=split,
            segment=segment,
            jobs=jobs,
            progress=True,
            callback=None,
            callback_arg=None,
        )

def demucs_main(music_file, save_dir='output/audio', background_file='output/audio/background.mp3', original_vocal_file='output/audio/vocal.mp3'):
    console = Console()
    
    # Ensure output directory exists
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # Load model
    console.print("🤖 Loading <htdemucs> model...")
    model = get_model('htdemucs')
    
    # Use fixed parameters
    separator = PreloadedSeparator(
        model=model,
        shifts=1,
        overlap=0.25,
        segment=None,
        split=True,
        jobs=0,
    )
    
    # Separate audio
    console.print("🎵 Separating audio...")
    _, outputs = separator.separate_audio_file(music_file)
    
    # Audio output parameters
    kwargs = {
        "samplerate": model.samplerate,
        "bitrate": 64,
        "preset": 4,
        "clip": "rescale",
        "as_float": False,
        "bits_per_sample": 16,
    }
    
    # Save vocals
    console.print("🎤 Saving vocals track...")
    save_audio(outputs['vocals'].cpu(), original_vocal_file, **kwargs)
    
    # Create and save background music
    console.print("🎹 Saving background music...")
    background = torch.zeros_like(outputs['vocals'])
    for source, audio in outputs.items():
        if source != 'vocals':
            background += audio
    save_audio(background.cpu(), background_file, **kwargs)
    
    console.print("[green]✨ Audio separation completed![/green]")

if __name__ == "__main__":
    demucs_main("output/audio/raw_full_audio.mp3")
