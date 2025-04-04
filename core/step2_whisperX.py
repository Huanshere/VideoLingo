import os,sys
import tempfile
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich import print as rprint

from core.config_utils import load_key
from core.all_whisper_methods.demucs_vl import demucs_main, RAW_AUDIO_FILE, VOCAL_AUDIO_FILE
from core.all_whisper_methods.audio_preprocess import process_transcription, convert_video_to_audio, split_audio, save_results, CLEANED_CHUNKS_EXCEL_PATH, normalize_audio_volume
from core.step1_ytdlp import find_video_files

NORMALIZED_VOCAL_PATH = "output/audio/normalized_vocals.wav"

def transcribe():
    if os.path.exists(CLEANED_CHUNKS_EXCEL_PATH):
        rprint("[yellow]⚠️ Transcription results already exist, skipping transcription step.[/yellow]")
        return
    
    # step0 Convert video to audio
    video_file = find_video_files()
    convert_video_to_audio(video_file)

    # step1 Demucs vocal separation:
    if load_key("demucs"):
        demucs_main()
        vocal_audio = normalize_audio_volume(VOCAL_AUDIO_FILE, NORMALIZED_VOCAL_PATH, format="mp3")
    else:
        vocal_audio = RAW_AUDIO_FILE

    # step2 Extract audio
    segments = split_audio(RAW_AUDIO_FILE)
    
    # step3 Transcribe audio
    all_results = []
    if load_key("whisper.runtime") == "local":
        from core.all_whisper_methods.whisperX_local import transcribe_audio as ts
        rprint("[cyan]🎤 Transcribing audio with local model...[/cyan]")
    else:
        from core.all_whisper_methods.whisperX_302 import transcribe_audio_302 as ts
        rprint("[cyan]🎤 Transcribing audio with 302 API...[/cyan]")

    for start, end in segments:
        result = ts(RAW_AUDIO_FILE, vocal_audio, start, end)
        all_results.append(result)
    
    # step4 Combine results
    combined_result = {'segments': []}
    for result in all_results:
        combined_result['segments'].extend(result['segments'])
    
    # step5 Process df
    df = process_transcription(combined_result)
    save_results(df)
        
if __name__ == "__main__":
    transcribe()