import os
import subprocess
import tempfile
from pathlib import Path
import torch
from rich.console import Console
from rich import print as rprint
from demucs.pretrained import get_model
import numpy as np
from demucs.audio import AudioFile, convert_audio_channels
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

# Separated at once. Memory use follows this, not the length of the video.
CHUNK_SECONDS = 300
# Audio on both sides of a chunk that the model hears and whose output is dropped
CONTEXT_SECONDS = 5

class StemWriter:
    """Encode a stem as MP3 through FFmpeg's libmp3lame while it is being separated.

    demucs.audio.save_audio encodes with lameenc, which writes no LAME/Xing header, so
    decoders cannot trim the encoder delay and the stem plays ~25 ms late. FFmpeg's
    header lets FFmpeg, pydub and soundfile decode it sample-aligned with raw.mp3.
    Without libmp3lame, fall back to PCM WAV content under the same name (as raw.mp3 does).
    """
    def __init__(self, path, samplerate, channels, bitrate="128k"):
        if _ffmpeg_has_encoder("libmp3lame"):
            codec = ["-c:a", "libmp3lame", "-b:a", bitrate, "-f", "mp3"]
        else:
            codec = ["-c:a", "pcm_s16le", "-f", "wav"]
        self.process = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(samplerate), "-ac", str(channels),
             "-i", "pipe:0", *codec, str(path)],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    def write(self, wav):
        try:
            self.process.stdin.write(wav.clamp(-1, 1).t().contiguous().numpy().astype("<f4").tobytes())
        except (BrokenPipeError, OSError):
            self.close()
            raise

    def close(self):
        _, stderr = self.process.communicate()
        if self.process.returncode:
            raise RuntimeError(f"FFmpeg could not write the stem: {stderr.decode('utf-8', errors='replace').strip()}")

def decode_pcm(audio_file, pcm_file, samplerate):
    """Decode to raw float32 and return the number of channels.

    FFmpeg trims the MP3 encoder delay of raw.mp3. Demucs' separate_audio_file() reads
    with sphn first, which keeps that delay and made the stems ~35 ms late relative to
    raw.mp3 (32 kHz LAME priming).
    """
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(audio_file), "-map", "0:a:0", "-threads", "1",
                    "-f", "f32le", "-ar", str(samplerate), str(pcm_file)], check=True, capture_output=True)
    return AudioFile(audio_file).channels(0)

def separate_in_chunks(separator, pcm_file, pcm_channels, samplerate, channels, vocal_writer, background_writer):
    frame_bytes = 4 * pcm_channels
    total = os.path.getsize(pcm_file) // frame_bytes
    chunk, context = CHUNK_SECONDS * samplerate, CONTEXT_SECONDS * samplerate
    for start in range(0, total, chunk):
        end = min(start + chunk, total)
        left, right = max(start - context, 0), min(end + context, total)
        if total > chunk:
            rprint(f"🎵 Separating {start // samplerate}s - {end // samplerate}s of {total // samplerate}s...")
        frames = np.fromfile(pcm_file, dtype="<f4", count=(right - left) * pcm_channels, offset=left * frame_bytes)
        wav = convert_audio_channels(torch.from_numpy(frames.astype(np.float32)).view(-1, pcm_channels).t(), channels)
        _, outputs = separator.separate_tensor(wav, samplerate)
        keep = slice(start - left, end - left)
        background = sum(audio for source, audio in outputs.items() if source != 'vocals')
        vocal_writer.write(outputs['vocals'][..., keep].cpu())
        background_writer.write(background[..., keep].cpu())
        del outputs, background, wav, frames
        gc.collect()

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
    # The stems are written next to their final place and moved there when they are
    # complete, so an interrupted run does not leave half a track behind.
    with tempfile.TemporaryDirectory(dir=_AUDIO_DIR) as tmp:
        pcm_file = Path(tmp) / "raw.f32le"
        vocal_file, background_file = Path(tmp) / "vocal.mp3", Path(tmp) / "background.mp3"
        pcm_channels = decode_pcm(_RAW_AUDIO_FILE, pcm_file, model.samplerate)
        vocal_writer = StemWriter(vocal_file, model.samplerate, model.audio_channels)
        background_writer = StemWriter(background_file, model.samplerate, model.audio_channels)
        try:
            separate_in_chunks(separator, pcm_file, pcm_channels, model.samplerate, model.audio_channels,
                               vocal_writer, background_writer)
        finally:
            for writer in (vocal_writer, background_writer):
                if writer.process.poll() is None:
                    writer.close()
        for writer in (vocal_writer, background_writer):
            writer.close()
        os.replace(vocal_file, _VOCAL_AUDIO_FILE)
        os.replace(background_file, _BACKGROUND_AUDIO_FILE)
    
    # Clean up memory
    del model, separator
    gc.collect()
    
    console.print("[green]✨ Audio separation completed![/green]")

if __name__ == "__main__":
    demucs_audio()
