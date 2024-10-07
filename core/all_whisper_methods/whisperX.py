import os
import sys
import whisperx
import torch
from typing import Dict
from rich import print as rprint
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from core.config_utils import load_key

MODEL_DIR = load_key("model_dir")

from core.all_whisper_methods.whisperXapi import (
    process_transcription, convert_video_to_audio, split_audio,
    save_results, save_language
)
from third_party.uvr5.uvr5_for_videolingo import uvr5_for_videolingo
    
def transcribe_audio(audio_file: str, start: float, end: float) -> Dict:
    WHISPER_LANGUAGE = load_key("whisper.language")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    rprint(f"[green]🚀 Starting WhisperX...[/green]")
    rprint(f"[cyan]Device:[/cyan] {device}")
    
    # Adjust batch size based on GPU memory
    if device == "cuda":
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # convert to GB
        if gpu_mem <= 6:
            batch_size = 2
            compute_type = "float16"
        elif gpu_mem <= 8:
            batch_size = 4
            compute_type = "float16"
        else:
            batch_size = 16
            compute_type = "float16"
        rprint(f"[cyan]GPU memory:[/cyan] {gpu_mem:.2f} GB, [cyan]Batch size:[/cyan] {batch_size}")
    else:
        batch_size = 4
        compute_type = "int8"
    
    rprint(f"[green]Starting WhisperX for segment {start:.2f}s to {end:.2f}s...[/green]")
    
    try:
        whisperx_model_dir = os.path.join(MODEL_DIR, "whisperx")
        if WHISPER_LANGUAGE == 'zh':
            model_name = "BELLE-2/Belle-whisper-large-v3-zh-punct"
        else:
            model_name = "large-v3"
        rprint(f"[green]Loading WHISPER model:[/green] {model_name} ...")

        try:
            model = whisperx.load_model(model_name, device, compute_type=compute_type, download_root=whisperx_model_dir)
        except Exception as e:
            rprint(f"[red]WhisperX model loading error:[/red]{e}\nMake sure you have downloaded the model first.")
            raise

        # Load audio segment using librosa
        import librosa
        audio, sample_rate = librosa.load(audio_file, sr=None, offset=start, duration=end-start)
        audio_segment = audio

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            transient=True
        ) as progress:
            task = progress.add_task("[cyan]Transcribing...", total=None)
            result = model.transcribe(audio_segment, batch_size=batch_size, language=(None if 'auto' in WHISPER_LANGUAGE else WHISPER_LANGUAGE))
            progress.update(task, completed=True)

        # Free GPU resources
        del model
        torch.cuda.empty_cache()

        # Save language
        save_language(result['language'])
        if result['language'] == 'zh' and WHISPER_LANGUAGE != 'zh':
            raise ValueError("WhisperX-large-v3 在中文转录方面表现不佳。请改用 'BELLE-2/Belle-whisper-large-v3-zh-punct' 模型。参考 'https://github.com/Huanshere/Videolingo/' 的说明")

        # Align whisper output
        model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
        result = whisperx.align(result["segments"], model_a, metadata, audio_segment, device, return_char_alignments=False)

        # Free GPU resources again
        del model_a
        torch.cuda.empty_cache()

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
    except Exception as e:
        rprint(f"[red]WhisperX processing error:[/red] {e}")
        raise

def transcribe(video_file: str):
    if not os.path.exists("output/log/cleaned_chunks.xlsx"):
        audio_file = convert_video_to_audio(video_file)

        # step1 UVR5 vocal separation
        output_dir = 'output/audio'
        if load_key("uvr_before_transcription"):
            if os.path.exists(os.path.join(output_dir, 'background.wav')):
                rprint(f"[yellow]{os.path.join(output_dir, 'background.wav')} already exists, skip uvr5 processing.[/yellow]")
            else:
                uvr5_for_videolingo(
                    os.path.join(output_dir, 'raw_full_audio.wav'),
                    output_dir,
                    os.path.join(output_dir, 'background.wav'),
                    os.path.join(output_dir, 'original_vocal.wav')
                )
                print("UVR5 processing completed, original_vocal.wav and background.wav saved")
            audio_file = os.path.join(output_dir, 'original_vocal.wav')
        else:
            audio_file = os.path.join(output_dir, 'raw_full_audio.wav')

        # step2 Extract audio
        segments = split_audio(audio_file)
        
        # step3 Transcribe audio
        all_results = []
        for start, end in segments:
            result = transcribe_audio(audio_file, start, end)
            all_results.append(result)
        
        # step4 Combine results
        combined_result = {'segments': []}
        for result in all_results:
            combined_result['segments'].extend(result['segments'])
        
        df = process_transcription(combined_result)
        save_results(df)
    else:
        rprint("[yellow]Transcription results already exist, skipping transcription step.[/yellow]")

if __name__ == "__main__":
    from core.step1_ytdlp import find_video_files
    video_file = find_video_files()
    rprint(f"[green]Found video file:[/green] {video_file}, [green]starting transcription...[/green]")
    transcribe(video_file)
