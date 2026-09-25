from core.utils import *
from core.asr_backend.audio_preprocess import process_transcription, convert_video_to_audio, prepare_audio_for_asr, split_audio, save_results, normalize_audio_volume
from core._1_ytdlp import find_media_file
from core.utils.models import *
from core.asr_backend import transcription_cache as cache

def local_backend(whisper):
    """Local ASR backend: "qwen" (default) or the optional "whisperx" fallback."""
    backend = str(whisper.get("backend", "qwen")).lower()
    if backend not in ("qwen", "whisperx"):
        raise ValueError(f"whisper.backend must be 'qwen' or 'whisperx', got {backend!r}")
    return backend

@check_file_exists(_2_CLEANED_CHUNKS)
def transcribe():
    runtime = load_key("whisper.runtime")
    if runtime not in ("local", "elevenlabs"):
        raise ValueError("Select local or elevenlabs for whisper.runtime. The 302.ai WhisperX cloud service has been retired.")
    # 1. prepare audio
    media_file, media_type = find_media_file()
    whisper = dict(load_key("whisper"))
    demucs = load_key("demucs")
    if runtime == "local":
        whisper["backend"] = local_backend(whisper)
        if whisper["backend"] == "qwen":
            from core.asr_backend import qwen_asr_local
            whisper["qwen_model"] = qwen_asr_local.model_size(whisper.get("qwen_model"))
            whisper["qwen_engine"] = qwen_asr_local.resolve_engine(whisper.get("qwen_engine"))
    key = cache.cache_key(media_file, whisper, demucs) if whisper.get("cache", True) else None
    cached = cache.read_result(key, "complete") if key else None
    if media_type == "video":
        convert_video_to_audio(media_file)
    else:
        prepare_audio_for_asr(media_file)

    # 2. Demucs vocal separation:
    if demucs:
        from core.asr_backend.demucs_vl import demucs_audio
        demucs_audio()
        vocal_audio = normalize_audio_volume(_VOCAL_AUDIO_FILE, _VOCAL_AUDIO_FILE, format="mp3")
    else:
        vocal_audio = _RAW_AUDIO_FILE

    # Downstream alignment/dubbing still needs the prepared audio on a cache hit.
    if cached:
        check_cancel()
        update_key("whisper.detected_language", cached["language"])
        save_results(process_transcription(cached["result"]))
        rprint("[green]Reused transcription from the content cache.[/green]")
        return

    # 3. Extract audio
    segments = split_audio(_RAW_AUDIO_FILE)
    
    # 4. Transcribe audio by clips
    all_results = []
    language = None
    if runtime == "local" and whisper["backend"] == "qwen":
        from core.asr_backend.qwen_asr_local import transcribe_audio as ts
        rprint(f"[cyan]🎤 Transcribing audio with local Qwen3-ASR {whisper['qwen_model']} + ForcedAligner...[/cyan]")
    elif runtime == "local":
        from core.asr_backend.whisperX_local import transcribe_audio as ts
        rprint("[cyan]🎤 Transcribing audio with local WhisperX (optional fallback)...[/cyan]")
    elif runtime == "elevenlabs":
        from core.asr_backend.elevenlabs_asr import transcribe_audio_elevenlabs as ts
        rprint("[cyan]🎤 Transcribing audio with ElevenLabs API...[/cyan]")
    else:
        raise ValueError(f"Unsupported ASR runtime: {runtime}")

    for start, end in segments:
        check_cancel()
        part = f"{start}_{end}"
        cached = cache.read_result(key, part) if key else None
        if cached:
            result = cached["result"]
            language = cached["language"]
        else:
            result = ts(_RAW_AUDIO_FILE, vocal_audio, start, end)
            check_cancel()
            language = whisper["language"] if whisper["language"] != "auto" else result.get("language")
            if key:
                cache.write_result(key, part, result, language)
        if language:
            update_key("whisper.detected_language", language)
        all_results.append(result)
    
    # 5. Combine results
    combined_result = {'segments': []}
    for result in all_results:
        combined_result['segments'].extend(result['segments'])
    
    # 6. Process df
    df = process_transcription(combined_result)
    check_cancel()
    save_results(df)
    if key:
        cache.write_result(key, "complete", combined_result, language)
        
if __name__ == "__main__":
    transcribe()
