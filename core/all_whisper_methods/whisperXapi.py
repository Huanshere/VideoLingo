import os
import sys
import replicate
import pandas as pd
import json
from typing import Dict, List, Tuple
import subprocess
import base64
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.config_utils import load_key
from moviepy.editor import AudioFileClip
import librosa
import soundfile as sf
import time

def convert_video_to_audio(input_file: str) -> str:
    audio_dir = 'output/audio'
    os.makedirs(audio_dir, exist_ok=True)
    audio_file = 'output/audio/raw_full_audio.wav'

    if not os.path.exists(audio_file):
        try:
            print(f"🎬➡️🎵 Converting to audio with librosa ......")
            # Load the audio from the video file
            y, sr = librosa.load(input_file, sr=16000)
            
            # Save the audio as a WAV file
            sf.write(audio_file, y, sr, subtype='PCM_16')
            
            print(f"🎬➡️🎵 Converted <{input_file}> to <{audio_file}> with librosa\n")
        except Exception as e:
            print(f"❌ Failed to convert <{input_file}> to <{audio_file}>.")
            print(f"Error: {str(e)}")
            raise

    return audio_file

def split_audio(audio_file: str, target_duration: int = 20*60, window: int = 60) -> List[Tuple[float, float]]:
    print("🔪 Splitting audio into segments...")
    
    # Use moviepy to get audio duration
    with AudioFileClip(audio_file) as audio:
        duration = audio.duration
    
    segments = []
    start = 0
    while start < duration:
        end = min(start + target_duration + window, duration)
        if end - start < target_duration:
            segments.append((start, end))
            break
        
        # Analyze audio in the 2-minute window
        window_start = start + target_duration - window
        window_end = min(window_start + 2 * window, duration)
        
        ffmpeg_cmd = ['ffmpeg', '-y', '-i', audio_file, '-ss', str(window_start), '-to', str(window_end), '-af', 'silencedetect=n=-30dB:d=0.5', '-f', 'null', '-']
        output = subprocess.run(ffmpeg_cmd, capture_output=True, text=True).stderr
        
        # Parse silence detection output
        silence_end_times = [float(line.split('silence_end: ')[1].split(' ')[0]) for line in output.split('\n') if 'silence_end' in line]
        
        if silence_end_times:
            # Find the first silence after the target duration
            split_point = next((t for t in silence_end_times if t > target_duration), None)
            if split_point:
                segments.append((start, start + split_point))
                start += split_point
                continue
        
        # If no suitable split point found, split at the target duration
        segments.append((start, start + target_duration))
        start += target_duration
    
    print(f"🔪 Split audio into {len(segments)} segments")
    return segments

def transcribe_segment(audio_file: str, start: float, end: float) -> Dict:
    print(f"🎙️ Transcribing segment from {start:.2f}s to {end:.2f}s")
    
    segment_file = f'output/audio/segment_{start:.2f}_{end:.2f}.mp3'
    ffmpeg_cmd = ['ffmpeg', '-y', '-i', audio_file, '-ss', str(start), '-to', str(end), '-ar', '16000', '-ac', '1', '-c:a', 'libmp3lame', '-b:a', '24k', segment_file]
    
    try:
        # Run ffmpeg command with timeout
        subprocess.run(ffmpeg_cmd, check=True, stderr=subprocess.PIPE, timeout=300)
    except subprocess.TimeoutExpired:
        print("⚠️ ffmpeg command timed out, retrying...")
        subprocess.run(ffmpeg_cmd, check=True, stderr=subprocess.PIPE)
    
    # Short wait to ensure file is written
    time.sleep(1)

    if not os.path.exists(segment_file):
        raise FileNotFoundError(f"Failed to create segment file: {segment_file}")

    # Encode to base64
    with open(segment_file, 'rb') as file:
        audio_base64 = base64.b64encode(file.read()).decode('utf-8')
    
    # Check segment size
    segment_size = len(audio_base64) / (1024 * 1024)  # Size in MB
    print(f"📊 Segment size: {segment_size:.2f} MB")

    result = transcribe_audio(audio_base64)
    
    # Delete segment file
    os.remove(segment_file)
    
    return result

def encode_file_to_base64(file_path: str) -> str:
    print("🔄 Encoding audio file to base64...")
    with open(file_path, 'rb') as file:
        encoded = base64.b64encode(file.read()).decode('utf-8')
        print("✅ File successfully encoded to base64")
        return encoded

def transcribe_audio(audio_base64: str) -> Dict:
    WHISPER_LANGUAGE = load_key("whisper.language")
    if WHISPER_LANGUAGE == 'zh':
        raise Exception("WhisperX API 不支持中文，如需翻译中文视频请本地部署 whisperX 模型，参阅 'https://github.com/Huanshere/VideoLingo/' 的说明文档.")
    client = replicate.Client(api_token=load_key("replicate_api_token"))
    print(f"🚀 Starting WhisperX API... Sometimes it takes time for the official server to start, please wait patiently... Actual processing speed is 10s for 2min audio, costing about ¥0.1 per run")
    try:
        input_params = {
            "debug": False,
            "vad_onset": 0.5,
            "audio_file": f"data:audio/wav;base64,{audio_base64}",
            "batch_size": 64,
            "vad_offset": 0.363,
            "diarization": False,
            "temperature": 0,
            "align_output": True,
            "language_detection_min_prob": 0,
            "language_detection_max_tries": 5
        }
        
        if 'auto' not in WHISPER_LANGUAGE:
            input_params["language"] = WHISPER_LANGUAGE
        
        output = client.run(
            "victor-upmeet/whisperx:84d2ad2d6194fe98a17d2b60bef1c7f910c46b2f6fd38996ca457afd9c8abfcb",
            input=input_params
        )
        return output
    except Exception as e:
        raise Exception(f"Error accessing whisperX API: {e} Please check your Replicate API key and internet connection.\n")

def process_transcription(result: Dict) -> pd.DataFrame:
    all_words = []
    for segment in result['segments']:
        for word in segment['words']:
            # ! For French, we need to convert guillemets to empty strings
            word["word"] = word["word"].replace('»', '').replace('«', '')
            
            if 'start' not in word and 'end' not in word:
                if all_words:
                    # Assign the end time of the previous word as the start and end time of the current word
                    word_dict = {
                        'text': word["word"],
                        'start': all_words[-1]['end'],
                        'end': all_words[-1]['end'],
                    }
                    all_words.append(word_dict)
                else:
                    # If it's the first word, look next for a timestamp then assign it to the current word
                    next_word = next((w for w in segment['words'] if 'start' in w and 'end' in w), None)
                    if next_word:
                        word_dict = {
                            'text': word["word"],
                            'start': next_word["start"],
                            'end': next_word["end"],
                        }
                        all_words.append(word_dict)
                    else:
                        raise Exception(f"No next word with timestamp found for the current word : {word}")
            else:
                # Normal case, with start and end times
                word_dict = {
                    'text': f'{word["word"]}',
                    'start': word.get('start', all_words[-1]['end'] if all_words else 0),
                    'end': word['end'],
                }
                
                all_words.append(word_dict)
    
    return pd.DataFrame(all_words)

def save_results(df: pd.DataFrame):
    os.makedirs('output/log', exist_ok=True)
    excel_path = os.path.join('output/log', "cleaned_chunks.xlsx")
    
    # Remove rows where 'text' is empty
    initial_rows = len(df)
    df = df[df['text'].str.len() > 0]
    removed_rows = initial_rows - len(df)
    if removed_rows > 0:
        print(f"ℹ️ Removed {removed_rows} row(s) with empty text.")
    
    # Check for and remove words longer than 20 characters
    long_words = df[df['text'].str.len() > 20]
    if not long_words.empty:
        print(f"⚠️ Warning: Detected {len(long_words)} word(s) longer than 20 characters. These will be removed.")
        df = df[df['text'].str.len() <= 20]
    
    df['text'] = df['text'].apply(lambda x: f'"{x}"')
    df.to_excel(excel_path, index=False)
    print(f"📊 Excel file saved to {excel_path}")

def save_language(language: str):
    os.makedirs('output/log', exist_ok=True)
    with open('output/log/transcript_language.json', 'w', encoding='utf-8') as f:
        json.dump({"language": language}, f, ensure_ascii=False, indent=4)
    
def transcribe(video_file: str):
    if not os.path.exists("output/log/cleaned_chunks.xlsx"):
        audio_file = convert_video_to_audio(video_file)
        print("!  Warning: This method does not apply UVR5 processing to the audio. Not recommended for videos with loud BGM.")
        # step2 Extract audio
        segments = split_audio(audio_file)
        
        # step3 Transcribe audio
        all_results = []
        for start, end in segments:
            result = transcribe_segment(audio_file, start, end)
            result['time_offset'] = start  # Add time offset to the result
            all_results.append(result)
        
        # step4 Combine results
        combined_result = {
            'segments': [],
            'detected_language': all_results[0]['detected_language']
        }
        for result in all_results:
            for segment in result['segments']:
                segment['start'] += result['time_offset']
                segment['end'] += result['time_offset']
                for word in segment['words']:
                    if 'start' in word:
                        word['start'] += result['time_offset']
                    if 'end' in word:
                        word['end'] += result['time_offset']
            combined_result['segments'].extend(result['segments'])
        
        # step5 Save language
        save_language(combined_result['detected_language'])
        
        # step6 Process transcription
        df = process_transcription(combined_result)
        save_results(df)
    else:
        print("📊 Transcription results already exist, skipping transcription step.")

if __name__ == "__main__":
    from core.step1_ytdlp import find_video_files
    video_file = find_video_files()
    print(f"🎬 Found video file: {video_file}, starting transcription...")
    transcribe(video_file)
