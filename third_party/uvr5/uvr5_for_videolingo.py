import os
import sys
import soundfile as sf
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from third_party.uvr5.vr import AudioPre, AudioPreDeEcho
import torch
import gc
from rich.console import Console
from rich.panel import Panel

console = Console()

def uvr5_for_videolingo(music_file, save_dir, background_file, original_vocal_file):
    from config import MODEL_DIR
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    console.print(Panel(f"[bold green]Starting UVR5 processing[/bold green]\nDevice: {device}"))
    
    # Step 1: Vocal separation
    console.print(Panel("[bold blue]Step 1: Vocal Separation[/bold blue]"))
    ap = AudioPre(agg=10, model_path=os.path.join(MODEL_DIR, "uvr5_weights", "HP2_all_vocals.pth"), device=device, is_half=False)
    ap._path_audio_(music_file, save_dir, save_dir, format='wav')
    
    # Rename files
    vocal_step1 = os.path.join(save_dir, f'vocal_{os.path.basename(music_file)}_10.wav')
    instrument_step1 = os.path.join(save_dir, f'instrument_{os.path.basename(music_file)}_10.wav')
    os.rename(vocal_step1, os.path.join(save_dir, 'vocal_step1.wav'))
    os.rename(instrument_step1, os.path.join(save_dir, 'instrument_step1.wav'))
    
    console.print("[green]Vocal separation completed[/green]")
    
    # Clear memory and CUDA cache
    del ap
    gc.collect()
    torch.cuda.empty_cache()
    console.print("[yellow]Memory cleared[/yellow]")
    
    # Step 2: De-echo on the vocal from step 1
    console.print(Panel("[bold blue]Step 2: De-echo Processing[/bold blue]"))
    ap_deecho = AudioPreDeEcho(agg=10, model_path=os.path.join(MODEL_DIR, "uvr5_weights", "VR-DeEchoAggressive.pth"), device=device, is_half=False)
    ap_deecho._path_audio_(os.path.join(save_dir, 'vocal_step1.wav'), save_dir, save_dir, format='wav')
    
    # Rename files
    vocal_step2 = os.path.join(save_dir, 'vocal_vocal_step1.wav_10.wav')
    instrument_step2 = os.path.join(save_dir, 'instrument_vocal_step1.wav_10.wav')
    os.rename(vocal_step2, original_vocal_file)
    os.rename(instrument_step2, os.path.join(save_dir, 'echo.wav'))
    
    console.print("[green]De-echo processing completed[/green]")
    
    # Clear memory and CUDA cache
    del ap_deecho
    gc.collect()
    torch.cuda.empty_cache()
    console.print("[yellow]Memory cleared[/yellow]")
    
    # Combine instruments from both steps to create background
    console.print(Panel("[bold blue]Step 3: Creating Background[/bold blue]"))
    instrument1, sr = sf.read(os.path.join(save_dir, 'instrument_step1.wav'))
    echo, _ = sf.read(os.path.join(save_dir, 'echo.wav'))
    background = instrument1 + echo
    sf.write(background_file, background, sr)
    
    console.print("[green]Background created[/green]")
    
    # Clean up intermediate files
    console.print(Panel("[bold blue]Cleaning up intermediate files[/bold blue]"))
    os.remove(os.path.join(save_dir, 'vocal_step1.wav'))
    os.remove(os.path.join(save_dir, 'instrument_step1.wav'))
    os.remove(os.path.join(save_dir, 'echo.wav'))
    
    console.print("[green]Intermediate files removed[/green]")
    
    # Final memory cleanup
    gc.collect()
    torch.cuda.empty_cache()
    console.print("[yellow]Final memory cleanup completed[/yellow]")
    
    console.print(Panel("[bold green]UVR5 processing completed successfully[/bold green]"))

if __name__ == '__main__':
    uvr5_for_videolingo(
        r'output\audio\raw_full_audio.wav',
        r'output\audio',
        r'output\audio\background.wav',
        r'output\audio\original_vocal.wav'
    )
