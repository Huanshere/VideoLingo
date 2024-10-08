import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from third_party.uvr5.vr import AudioPre, AudioPreDeEcho
import torch
import gc
from rich.console import Console
from rich.panel import Panel
from pydub import AudioSegment
from core.config_utils import load_key

console = Console()

def process_segment(segment_file, save_dir, device, model_dir, segment_index):
    console.print(Panel(f"[bold blue]Processing segment {segment_index}: {os.path.basename(segment_file)}[/bold blue]"))
    
    # Step 1: Vocal separation
    console.print("[cyan]Starting vocal separation...[/cyan]")
    ap = AudioPre(agg=10, model_path=os.path.join(model_dir, "uvr5_weights", "HP2_all_vocals.pth"), device=device, is_half=False)
    ap._path_audio_(segment_file, save_dir, save_dir, format='wav')
    
    console.print("[cyan]Renaming files after vocal separation...[/cyan]")
    vocal_step1 = os.path.join(save_dir, f'vocal_{os.path.basename(segment_file)}_10.wav')
    instrument_step1 = os.path.join(save_dir, f'instrument_{os.path.basename(segment_file)}_10.wav')
    os.rename(vocal_step1, os.path.join(save_dir, f'vocal_step1_{segment_index}.wav'))
    os.rename(instrument_step1, os.path.join(save_dir, f'instrument_step1_{segment_index}.wav'))
    
    del ap
    gc.collect()
    torch.cuda.empty_cache()
    
    # Step 2: De-echo on the vocal from step 1
    console.print("[cyan]Starting de-echo process...[/cyan]")
    ap_deecho = AudioPreDeEcho(agg=10, model_path=os.path.join(model_dir, "uvr5_weights", "VR-DeEchoAggressive.pth"), device=device, is_half=False)
    ap_deecho._path_audio_(os.path.join(save_dir, f'vocal_step1_{segment_index}.wav'), save_dir, save_dir, format='wav')
    
    vocal_step2 = os.path.join(save_dir, f'vocal_vocal_step1_{segment_index}.wav_10.wav')
    instrument_step2 = os.path.join(save_dir, f'instrument_vocal_step1_{segment_index}.wav_10.wav')
    os.rename(vocal_step2, os.path.join(save_dir, f'final_vocal_{segment_index}.wav'))
    os.rename(instrument_step2, os.path.join(save_dir, f'echo_{segment_index}.wav'))
    
    del ap_deecho
    gc.collect()
    torch.cuda.empty_cache()

def uvr5_for_videolingo(music_file, save_dir, background_file, original_vocal_file):
    MODEL_DIR = load_key("model_dir")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    console.print(Panel(f"[bold green]Starting UVR5 processing[/bold green]\nDevice: {device}"))
    
    # Load the full audio file
    audio = AudioSegment.from_wav(music_file)
    segment_duration = 10 * 60 * 1000  # 10 minutes in milliseconds

    # Process audio in 10-minute segments
    segment_count = 0
    for start in range(0, len(audio), segment_duration):
        end = min(start + segment_duration, len(audio))
        segment = audio[start:end]
        
        # Process the segment
        segment_file = os.path.join(save_dir, f"segment_{start//1000}_{end//1000}.wav")
        segment.export(segment_file, format="wav")
        
        process_segment(segment_file, save_dir, device, MODEL_DIR, segment_count)
        
        # Clean up segment file
        os.remove(segment_file)
        segment_count += 1

    # Combine all processed segments
    final_vocal = AudioSegment.empty()
    final_background = AudioSegment.empty()

    for i in range(segment_count):
        vocal = AudioSegment.from_wav(os.path.join(save_dir, f'final_vocal_{i}.wav'))
        instrument = AudioSegment.from_wav(os.path.join(save_dir, f'instrument_step1_{i}.wav'))
        echo = AudioSegment.from_wav(os.path.join(save_dir, f'echo_{i}.wav'))
        
        final_vocal += vocal
        # Overlay echo on instrument instead of adding
        background_segment = instrument.overlay(echo)
        final_background += background_segment

    # Export the final files with compression
    export_params = {
        "format": "wav",
        "parameters": ["-acodec", "pcm_s16le", "-ar", "16000"]
    }
    final_vocal.export(original_vocal_file, **export_params)
    final_background.export(background_file, **export_params)

    # Clean up intermediate files
    for i in range(segment_count):
        os.remove(os.path.join(save_dir, f'vocal_step1_{i}.wav'))
        os.remove(os.path.join(save_dir, f'instrument_step1_{i}.wav'))
        os.remove(os.path.join(save_dir, f'final_vocal_{i}.wav'))
        os.remove(os.path.join(save_dir, f'echo_{i}.wav'))

    console.print(Panel("[bold green]UVR5 processing completed successfully[/bold green]"))

if __name__ == '__main__':
    uvr5_for_videolingo(
        'output/audio/raw_full_audio.wav',
        'output/audio',
        'output/audio/background.wav',
        'output/audio/original_vocal.wav'
    )