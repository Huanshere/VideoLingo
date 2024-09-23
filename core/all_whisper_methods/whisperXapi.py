import os
import sys
import replicate
import pandas as pd
import json
from typing import Dict, List, Tuple
import subprocess
import base64
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def convert_video_to_audio(input_file: str) -> str:
    os.makedirs('output/audio', exist_ok=True)
    audio_file = 'output/audio/raw_full_audio'
    audio_file_with_format = f'{audio_file}.wav'

    if not os.path.exists(f'{audio_file}.wav'):
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', input_file,
            '-vn',
            '-acodec', 'libmp3lame',
            '-ar', '16000',
            '-b:a', '64k',
            f'{audio_file}.wav'
        ]
        try:
            print(f"🎬➡️🎵 Converting to audio with libmp3lame ......")
            subprocess.run(ffmpeg_cmd, check=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            print(f"🎬➡️🎵 Converted <{input_file}> to <{f'{audio_file}.wav'}> with libmp3lame\n")
            audio_file_with_format = f'{audio_file}.wav'

        except subprocess.CalledProcessError as e:
            print("❌ libmp3lame failed. Retrying with aac ......")
            print(f"Error output: {e.stderr.decode()}")

            # 有时候会遇到ffmpeg不含libmp3lame解码器的错误，使用内置 flac无损编码 兜底进行音频转换的 fallback ffmpeg 命令
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', input_file,
                '-vn',
                '-acodec', 'flac',
                '-ar', '16000',
                '-b:a', '64k',
                f'{audio_file}.flac'
            ]

            try:
                subprocess.run(ffmpeg_cmd, check=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                print(f"🎬➡️🎵 Converted <{input_file}> to <{f'{audio_file}.flac'}> with aac\n")
                audio_file_with_format = f'{audio_file}.flac'

            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to convert <{input_file}> to <{f'{audio_file}.flac'}> with both libmp3lame and aac.")
                print(f"Error output: {e.stderr.decode()}")
                raise

    return audio_file_with_format

def split_audio(audio_file: str, target_duration: int = 20*60, window: int = 60) -> List[Tuple[float, float]]:
    print("🔪 Splitting audio into segments...")
    duration = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', audio_file]).decode('utf-8').strip())
    
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
        
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', audio_file,
            '-ss', str(window_start),
            '-to', str(window_end),
            '-af', 'silencedetect=n=-30dB:d=0.5',
            '-f', 'null',
            '-'
        ]
        
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
    #! Occasionally, the process may pause here. Warning the user to skip the pause.
    print(f"!!! YOU SHOULD SEE [🚀 Starting WhisperX API...] in the next step in 3 secs, otherwise hit ENTER to skip the pause.")
    return segments

import time
def transcribe_segment(audio_file: str, start: float, end: float) -> Dict:
    print(f"🎙️ Transcribing segment from {start:.2f}s to {end:.2f}s")
    
    #! Occasionally, the process may pause here. Adding a short delay to ensure stability.
    time.sleep(1)
    segment_file = f'output/audio/segment_{start:.2f}_{end:.2f}.wav'
    ffmpeg_cmd = [
        'ffmpeg',
        '-i', audio_file,
        '-ss', str(start),
        '-to', str(end),
        '-c', 'copy',
        segment_file
    ]
    subprocess.run(ffmpeg_cmd, check=True, stderr=subprocess.PIPE)
    time.sleep(1)

    # Encode to base64
    with open(segment_file, 'rb') as file:
        audio_base64 = base64.b64encode(file.read()).decode('utf-8')
    
    # Check segment size
    segment_size = len(audio_base64) / (1024 * 1024)  # Size in MB
    print(f"📊 Segment size: {segment_size:.2f} MB")

    result = transcribe_audio(audio_base64)
    
    # delete the segment file
    os.remove(segment_file)
    
    return result

def encode_file_to_base64(file_path: str) -> str:
    print("🔄 Encoding audio file to base64...")
    with open(file_path, 'rb') as file:
        encoded = base64.b64encode(file.read()).decode('utf-8')
        print("✅ File successfully encoded to base64")
        return encoded

def transcribe_audio(audio_base64: str) -> Dict:
    from config import WHISPER_LANGUAGE
    from config import REPLICATE_API_TOKEN
    # Set API token
    os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN
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
        
        if WHISPER_LANGUAGE != 'auto':
            input_params["language"] = WHISPER_LANGUAGE
        
        output = replicate.run(
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
        
        segments = split_audio(audio_file)
        
        all_results = []
        for start, end in segments:
            result = transcribe_segment(audio_file, start, end)
            result['time_offset'] = start  # Add time offset to the result
            all_results.append(result)
        
        # Combine results
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
        
        save_language(combined_result['detected_language'])
        
        df = process_transcription(combined_result)
        save_results(df)
    else:
        print("📊 Transcription results already exist, skipping transcription step.")

if __name__ == "__main__":
    from core.step1_ytdlp import find_video_files
    video_file = find_video_files()
    print(f"🎬 Found video file: {video_file}, starting transcription...")
    transcribe(video_file)
