# ! 请在此处停下 仍在开发中

import re
import subprocess
from pydub import AudioSegment
import os, sys, json, shutil
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from third_party.uvr5.uvr5_for_videolingo import uvr5_for_videolingo
from rich import print as rprint
from rich.panel import Panel
from rich.console import Console
from rich.progress import Progress

console = Console()

def parse_srt(srt_content):
    pattern = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n((?:.+\n)+)')
    matches = pattern.findall(srt_content)
    return [{'index': int(m[0]), 'start': m[1], 'end': m[2], 'text': m[3].strip()} for m in matches]  # 解析SRT内容

def time_to_ms(time_str):
    h, m, s = time_str.split(':')
    s, ms = s.split(',')
    return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)  # 将时间字符串转换为毫秒

def extract_audio(input_video, start_time, end_time, output_file):
    start_ms = time_to_ms(start_time)
    end_ms = time_to_ms(end_time)
    
    temp_audio = 'temp_audio.wav'
    with console.status("[bold green]Extracting audio..."):
        subprocess.run(['ffmpeg', '-i', input_video, '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2', temp_audio], check=True)
    
    audio = AudioSegment.from_wav(temp_audio)
    extract = audio[start_ms:end_ms]
    extract.export(output_file, format="wav")
    
    os.remove(temp_audio)

def step8_main(input_video):
    if os.path.exists('output/audio/background.wav'):
        rprint(Panel("output/audio/background.wav already exists, skip.", title="Info", border_style="blue"))
        return
    
    # step1 提取 5s 参考音频
    with open('output/audio/src_subs_for_audio.srt', 'r', encoding='utf-8') as f:
        srt_content = f.read()  
    subtitles = parse_srt(srt_content)
    target_subtitle = None
    skipped = 0
    for subtitle in subtitles:
        if skipped < 2:
            skipped += 1
            continue
        duration = time_to_ms(subtitle['end']) - time_to_ms(subtitle['start'])
        if duration > 5000:
            target_subtitle = subtitle
            break
    
    if not target_subtitle:
        target_subtitle = subtitles[2] if len(subtitles) > 2 else subtitles[0]
        
    if target_subtitle:
        rprint(Panel.fit(f"Selected subtitle: {target_subtitle['text']}\nStart time: {target_subtitle['start']}\nEnd time: {target_subtitle['end']}", title="Subtitle Info"))
        
        cleaned_text = re.sub(r'[\\/*?:"<>|]', '', target_subtitle['text'])
        audio_filename = f"output/audio/{cleaned_text}.wav"
        extract_audio(input_video, target_subtitle['start'], target_subtitle['end'], audio_filename)
        with console.status("[bold green]Processing audio with uvr5_for_videolingo..."):
            uvr5_for_videolingo(audio_filename, 'output/audio')
        os.remove(f"output/audio/instrument_{os.path.basename(audio_filename)}_10.wav")  # 清理临时文件 🧹
        os.remove(audio_filename)  # 清理临时文件 🧹
        os.rename(f"output/audio/vocal_{os.path.basename(audio_filename)}_10.wav", audio_filename)  # 重命名文件 📛
        
        from config import MODEL_DIR, DUBBING_CHARACTER
        SOVITS_MODEL_PATH = os.path.join(MODEL_DIR, "GPT_SoVITS", "trained", DUBBING_CHARACTER)
        for file in os.listdir(SOVITS_MODEL_PATH):
            if file.endswith((".wav", ".mp3")):
                os.remove(os.path.join(SOVITS_MODEL_PATH, file))

        shutil.move(audio_filename, os.path.join(SOVITS_MODEL_PATH, os.path.basename(audio_filename)))  # 移动文件到指定目录
        
        with open(os.path.join(SOVITS_MODEL_PATH, "infer_config.json"), 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        config["emotion_list"]["default"]["ref_wav_path"] = os.path.basename(audio_filename)
        config["emotion_list"]["default"]["prompt_text"] = os.path.basename(audio_filename).replace(".wav", "")

        #TODO 设置语言
        from core.step2_whisper import get_whisper_language
        from config import WHISPER_LANGUAGE
        language = get_whisper_language() if WHISPER_LANGUAGE == 'auto' else WHISPER_LANGUAGE
        config["emotion_list"]["default"]["prompt_language"] = 'zh' if 'zh' in language else 'en'
        
        with open(os.path.join(SOVITS_MODEL_PATH, "infer_config.json"), 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)

        rprint(Panel(f"Audio extracted and cleaned and saved as {audio_filename}", title="Success", border_style="green"))
    else:
        rprint(Panel("No subtitles found.", title="Warning", border_style="yellow"))

    # step2 提取完整音频
    full_audio_path = 'output/audio/full_audio.wav'
    with console.status("[bold green]Extracting full audio..."):
        subprocess.run(['ffmpeg', '-i', input_video, '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2', full_audio_path], check=True)
    with console.status("[bold green]Processing full audio with uvr5_for_videolingo..."):
        uvr5_for_videolingo(full_audio_path, 'output/audio')
    os.remove(full_audio_path)  # 清理临时文件 🧹
    os.rename('output/audio/vocal_full_audio.wav_10.wav', 'output/audio/original_vocal.wav')  # 重命名文件 📛
    os.rename('output/audio/instrument_full_audio.wav_10.wav', 'output/audio/background.wav')  # 重命名文件 📛
    rprint(Panel("Full audio extracted and cleaned and saved as original_vocal.wav and background.wav", title="Success", border_style="green"))

if __name__ == "__main__":
    from core.step1_ytdlp import find_video_files
    input_video = find_video_files()
    step8_main(input_video)