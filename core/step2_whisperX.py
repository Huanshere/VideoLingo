import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich import print as rprint

from core.config_utils import load_key
from core.all_whisper_methods.demucs_vl import demucs_main, RAW_AUDIO_FILE, VOCAL_AUDIO_FILE
from core.all_whisper_methods.audio_preprocess import process_transcription, convert_video_to_audio, split_audio, save_results, compress_audio, CLEANED_CHUNKS_EXCEL_PATH
from core.step1_ytdlp import find_video_files
from core.all_whisper_methods.audio_preprocess import normalize_audio_volume

WHISPER_FILE = "output/audio/for_whisper.mp3"
ENHANCED_VOCAL_PATH = "output/audio/enhanced_vocals.mp3"

def enhance_vocals():
    """Enhance vocals audio volume using audio normalization"""
    try:
        rprint("[cyan]🎙️ Normalizing vocals audio...[/cyan]")
        normalized_path = normalize_audio_volume(
            VOCAL_AUDIO_FILE,
            ENHANCED_VOCAL_PATH
        )
        return normalized_path
    except Exception as e:
        rprint(f"[red]Error normalizing vocals: {str(e)}[/red]")
        return VOCAL_AUDIO_FILE
    
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
    
    # step2 Compress audio
    raw_audio = RAW_AUDIO_FILE
    vocal_audio = enhance_vocals() if load_key("demucs") else RAW_AUDIO_FILE
    raw_compressed = compress_audio(raw_audio, WHISPER_FILE)
    vocal_compressed = compress_audio(vocal_audio, WHISPER_FILE)

    # step3 Extract audio
    segments = split_audio(raw_compressed)
    
    # step4 Transcribe audio
    all_results = []
    if load_key("whisper.runtime") == "local":
        from core.all_whisper_methods.whisperX_local import transcribe_audio as ts
        rprint("[cyan]🎤 Transcribing audio with local model...[/cyan]")
    else:
        from core.all_whisper_methods.whisperX_302 import transcribe_audio_302 as ts
        rprint("[cyan]🎤 Transcribing audio with 302 API...[/cyan]")

    for start, end in segments:
        result = ts(raw_compressed,vocal_compressed, start, end)
        all_results.append(result)
    
    # step5 Combine results
    combined_result = {'segments': []}
    for result in all_results:
        combined_result['segments'].extend(result['segments'])
    
    # step6 Process df
    df = process_transcription(combined_result)
    save_results(df)
        
if __name__ == "__main__":
    transcribe()