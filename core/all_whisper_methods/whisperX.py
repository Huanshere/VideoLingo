import os
import sys
import whisperx
import torch
from typing import Dict

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import MODEL_DIR
from core.all_whisper_methods.whisperXapi import (
    process_transcription, convert_video_to_audio, split_audio,
    save_results, save_language
)

def transcribe_audio(audio_file: str, start: float, end: float) -> Dict:
    from config import WHISPER_LANGUAGE
    device = "cuda" if torch.cuda.is_available() else "cpu"
    batch_size = 16  # TODO Reduce this value if GPU memory is insufficient
    compute_type = "float16"  # TODO Change to "int8" if GPU memory is insufficient (may reduce accuracy)
    print(f"🚀 Starting WhisperX for segment {start:.2f}s to {end:.2f}s... Please wait patiently...")
    try:
        whisperx_model_dir = os.path.join(MODEL_DIR, "whisperx")
        model = whisperx.load_model("large-v2", device, compute_type=compute_type, download_root=whisperx_model_dir)

        # Load audio segment
        audio = whisperx.load_audio(audio_file)
        audio_segment = audio[int(start * 16000):int(end * 16000)]  # Assuming 16kHz sample rate

        result = model.transcribe(audio_segment, batch_size=batch_size, language=(None if WHISPER_LANGUAGE == 'auto' else WHISPER_LANGUAGE))
        # Free GPU resources
        del model
        torch.cuda.empty_cache()

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
                word['start'] += start
                word['end'] += start

        return result
    except Exception as e:
        raise Exception(f"WhisperX processing error: {e}")

def transcribe(video_file: str):
    if not os.path.exists("output/log/cleaned_chunks.xlsx"):
        audio_file = convert_video_to_audio(video_file)
        
        segments = split_audio(audio_file)
        
        all_results = []
        for start, end in segments:
            result = transcribe_audio(audio_file, start, end)
            all_results.append(result)
        
        # Combine results
        combined_result = {
            'segments': [],
            'language': all_results[0]['language']
        }
        for result in all_results:
            combined_result['segments'].extend(result['segments'])
        
        save_language(combined_result['language'])
        
        df = process_transcription(combined_result)
        save_results(df)
    else:
        print("📊 Transcription results already exist, skipping transcription step.")

if __name__ == "__main__":
    from core.step1_ytdlp import find_video_files
    video_file = find_video_files()
    print(f"🎬 Found video file: {video_file}, starting transcription...")
    transcribe(video_file)
