import os
import sys
import whisperx
import torch
from typing import Dict
from rich import print as rprint

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import MODEL_DIR
from core.all_whisper_methods.whisperXapi import (
    process_transcription, convert_video_to_audio, split_audio,
    save_results, save_language
)

def transcribe_audio(audio_file: str, start: float, end: float) -> Dict:
    from config import WHISPER_LANGUAGE
    device = "cuda" if torch.cuda.is_available() else "cpu"
    rprint(f"[green]🚀 Starting WhisperX...[/green]")
    rprint(f"[cyan]Device:[/cyan] {device}")
    
    # Adjust batch size based on GPU memory
    if device == "cuda":
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # convert to GB
        batch_size = 4 if gpu_mem <= 8 else 16
        compute_type = "float16"  # Change to "int8" if GPU memory is still insufficient (may reduce accuracy)
        rprint(f"[cyan]GPU memory:[/cyan] {gpu_mem:.2f} GB, [cyan]Batch size:[/cyan] {batch_size}")
    else:
        batch_size = 4
    
    rprint(f"[green]Starting WhisperX for segment {start:.2f}s to {end:.2f}s...[/green]")
    
    try:
        whisperx_model_dir = os.path.join(MODEL_DIR, "whisperx")
        model_name = "large-v3" if WHISPER_LANGUAGE not in ["zh", "yue"] else "BELLE-2/Belle-whisper-large-v3-zh-punct"
        rprint(f"[green]Loading WHISPER model:[/green] {model_name} ...")
        model = whisperx.load_model(model_name, device, compute_type=compute_type, download_root=whisperx_model_dir)

        # Load audio segment
        audio = whisperx.load_audio(audio_file)
        audio_segment = audio[int(start * 16000):int(end * 16000)]  # Assuming 16kHz sample rate

        result = model.transcribe(audio_segment, batch_size=batch_size, language=(None if WHISPER_LANGUAGE == 'auto' else WHISPER_LANGUAGE))
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
        
        segments = split_audio(audio_file)
        
        all_results = []
        for start, end in segments:
            result = transcribe_audio(audio_file, start, end)
            all_results.append(result)
        
        # Combine results
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
