import os,sys
import tempfile
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich import print as rprint

from core.config_utils import load_key
from core.all_whisper_methods.demucs_vl import demucs_main, RAW_AUDIO_FILE, VOCAL_AUDIO_FILE
from core.all_whisper_methods.audio_preprocess import process_transcription, convert_video_to_audio, split_audio, save_results, compress_audio, CLEANED_CHUNKS_EXCEL_PATH
from core.step1_ytdlp import find_video_files
from core.all_whisper_methods.audio_preprocess import normalize_audio_volume

RAW_COMPRESSED_AUDIO_PATH = "output/audio/raw_compressed.mp3"
VOCAL_COMPRESSED_AUDIO_PATH = "output/audio/vocal_compressed.mp3"
NORMALIZED_VOCAL_PATH = "output/audio/normalized_vocals.mp3"
NORMALIZED_RAW_PATH = "output/audio/normalized_raw.mp3"

def process_audio(input_path, output_path, normalize=True):
    """
    normalized and compressed audio
    """
    if normalize:
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=True) as temp_file:
            normalized_path = temp_file.name
            temp_file.close()
            try:
                normalize_audio_volume(input_path, normalized_path, format="mp3")
                compress_audio(normalized_path, output_path)
            finally:
                if os.path.exists(normalized_path):
                    os.remove(normalized_path)
    else:
        compress_audio(input_path, output_path)
    return output_path

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
    raw_audio = process_audio(RAW_AUDIO_FILE, RAW_COMPRESSED_AUDIO_PATH, normalize=False)
    vocal_audio = process_audio(VOCAL_AUDIO_FILE, VOCAL_COMPRESSED_AUDIO_PATH, normalize=True) if load_key("demucs") else raw_audio

    # step3 Extract audio
    segments = split_audio(raw_audio)
    
    # step4 Transcribe audio
    all_results = []
    if load_key("whisper.runtime") == "local":
        from core.all_whisper_methods.whisperX_local import transcribe_audio as ts
        rprint("[cyan]🎤 Transcribing audio with local model...[/cyan]")
    else:
        from core.all_whisper_methods.whisperX_302 import transcribe_audio_302 as ts
        rprint("[cyan]🎤 Transcribing audio with 302 API...[/cyan]")

    for start, end in segments:
        result = ts(raw_audio,vocal_audio, start, end)
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