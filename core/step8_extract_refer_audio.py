import re
import subprocess
from pydub import AudioSegment
import os,sys, json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from uvr5.uvr5_for_submagic import uvr5_for_submagic

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
    
    # 将视频转换为音频
    temp_audio = 'temp_audio.wav'
    subprocess.run([
        'ffmpeg', '-i', input_video, '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2', temp_audio
    ], check=True)
    
    # 提取特定部分音频
    audio = AudioSegment.from_wav(temp_audio)
    extract = audio[start_ms:end_ms]
    extract.export(output_file, format="wav")
    
    # 清理临时文件
    os.remove(temp_audio)

def step8_main(input_video, DUBBING_CHARACTER = "Huanyu"):
    # 如果'output/audio/background.wav'存在，则return跳过
    if os.path.exists('output/audio/background.wav'):
        print('output/audio/background.wav already exists, skip.')
        return
    # 读取SRT文件内容
    with open('output/audio/english_subtitles_for_audio.srt', 'r', encoding='utf-8') as f:
        srt_content = f.read()  
    subtitles = parse_srt(srt_content)
    
    # step1: 选择并提取第一个大于5秒的字幕 跳过前两个（很多时候第一个会有问题）
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
        print(f"Selected subtitle: {target_subtitle['text']}")  # 选择的字幕
        print(f"Start time: {target_subtitle['start']}")  # 开始时间
        print(f"End time: {target_subtitle['end']}")  # 结束时间
        
        # 使用字幕内容命名音频文件，并移除非法字符
        cleaned_text = re.sub(r'[\\/*?:"<>|]', '', target_subtitle['text'])
        audio_filename = f"output/audio/{cleaned_text}.wav"
        extract_audio(input_video, target_subtitle['start'], target_subtitle['end'], audio_filename)
        print('Starting uvr5_for_submagic...')  # 开始处理音频
        uvr5_for_submagic(audio_filename, 'output/audio')
        os.remove(f"output/audio/instrument_{os.path.basename(audio_filename)}_10.wav")  # 清理临时文件 🧹
        os.remove(audio_filename)  # 清理临时文件 🧹
        os.rename(f"output/audio/vocal_{os.path.basename(audio_filename)}_10.wav", audio_filename)  # 重命名文件 📛
        # remove any wav or mp3 under # move to GPT-SoVITS-Inference/trained/{DUBBING_CHARACTER}
        for file in os.listdir(f"GPT-SoVITS-Inference/trained/{DUBBING_CHARACTER}"):
            if file.endswith(".wav") or file.endswith(".mp3"):
                os.remove(f"GPT-SoVITS-Inference/trained/{DUBBING_CHARACTER}/{file}")

        # === 接下来是将音频文件移动到GPT-SoVITS-Inference/trained/{DUBBING_CHARACTER} ===
        # move to GPT-SoVITS-Inference/trained/{DUBBING_CHARACTER}
        os.rename(audio_filename, f"GPT-SoVITS-Inference/trained/{DUBBING_CHARACTER}/{os.path.basename(audio_filename)}")  # 重命名文件 📛
        
        # 完成TODO部分
        with open(f"GPT-SoVITS-Inference/trained/{DUBBING_CHARACTER}/infer_config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        config["emotion_list"]["default"]["ref_wav_path"] = os.path.basename(audio_filename)
        config["emotion_list"]["default"]["prompt_text"] = os.path.basename(audio_filename).replace(".wav", "")
        
        with open(f"GPT-SoVITS-Inference/trained/{DUBBING_CHARACTER}/infer_config.json", 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)

        print(f"Audio extracted and cleaned and saved as {audio_filename}")  # 音频处理完成
    else:
        print("No subtitles found.")  # 未找到字幕

    # step2: 提取整个视频的音频
    full_audio_path = 'output/audio/full_audio.wav'
    print("Extracting full audio...")  # 提取完整音频
    subprocess.run([
        'ffmpeg', '-i', input_video, '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2', full_audio_path
    ], check=True)
    print('Starting uvr5_for_submagic for full audio...')  # 开始处理完整音频
    uvr5_for_submagic(full_audio_path, 'output/audio')
    os.remove(full_audio_path)  # 清理临时文件 🧹
    os.rename('output/audio/vocal_full_audio.wav_10.wav', 'output/audio/original_vocal.wav')  # 重命名文件 📛
    os.rename('output/audio/instrument_full_audio.wav_10.wav', 'output/audio/background.wav')  # 重命名文件 📛
    print("Full audio extracted and cleaned and saved as original_vocal.wav and background.wav")  # 完整音频处理完成

if __name__ == "__main__":
    import glob  
    input_video = (glob.glob("*.mp4") + glob.glob("*.webm"))[0]
    step8_main(input_video)