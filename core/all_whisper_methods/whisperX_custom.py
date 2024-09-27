import os
import sys
import whisperx
import torch
from typing import Dict
from rich import print as rprint
from transformers import WhisperForConditionalGeneration, WhisperProcessor

HF_MODEL_NAME = "BELLE-2/Belle-whisper-large-v3-zh-punct"

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import MODEL_DIR, WHISPER_LANGUAGE
from core.all_whisper_methods.whisperXapi import (
    process_transcription, convert_video_to_audio, split_audio,
    save_results, save_language
)

def transcribe_audio(audio_file: str, start: float, end: float) -> Dict:
    from config import WHISPER_LANGUAGE
    device = "cuda" if torch.cuda.is_available() else "cpu"
    rprint(f"[green]🚀 Starting Hugging Face Whisper...[/green]")
    rprint(f"[cyan]Device:[/cyan] {device}")
    
    # Adjust batch size based on GPU memory
    if device == "cuda":
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # convert to GB
        batch_size = 4 if gpu_mem <= 8 else 16
        compute_type = "float16"  # Change to "int8" if GPU memory is still insufficient (may reduce accuracy)
        rprint(f"[cyan]GPU memory:[/cyan] {gpu_mem:.2f} GB, [cyan]Batch size:[/cyan] {batch_size}")
    else:
        batch_size = 4
        compute_type = "int8"
    
    rprint(f"[green]Starting Hugging Face Whisper for segment {start:.2f}s to {end:.2f}s...[/green]")
    
    try:
        # Load Hugging Face model
        model = WhisperForConditionalGeneration.from_pretrained(HF_MODEL_NAME).to(device)
        processor = WhisperProcessor.from_pretrained(HF_MODEL_NAME)

        # Load audio segment
        audio = whisperx.load_audio(audio_file)
        audio_segment = audio[int(start * 16000):int(end * 16000)]  # Assuming 16kHz sample rate

        # Process audio
        input_features = processor(audio_segment, sampling_rate=16000, return_tensors="pt").input_features.to(device)

        # Generate tokens
        forced_decoder_ids = processor.get_decoder_prompt_ids(language=WHISPER_LANGUAGE, task="transcribe")
        generated_ids = model.generate(input_features, forced_decoder_ids=forced_decoder_ids)

        # Decode output
        transcription = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

        # Create a compatible result format
        result = {
            "segments": [{"text": transcription, "start": start, "end": end}],
            "language": WHISPER_LANGUAGE
        }

        # Free GPU resources
        del model
        torch.cuda.empty_cache()

        # Save language
        save_language(result['language'])

        # Note: Skipping WhisperX alignment step as it might be incompatible with Hugging Face models
        # If alignment is needed, consider implementing or using other tools

        return result
    except Exception as e:
        rprint(f"[red]Hugging Face Whisper processing error:[/red] {e}")
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
