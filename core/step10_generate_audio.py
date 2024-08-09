import os
import pandas as pd
from tqdm import tqdm
import urllib.parse
import requests
import librosa
import soundfile as sf
import os, sys
import time
import subprocess
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MIN_SUBTITLE_DURATION, step9_trim_model, DUBBNING_CHARACTER
import psutil
from core.prompts_storage import get_subtitle_trim_prompt
from core.ask_gpt import ask_gpt

def ping_tts_service():
    url = 'http://127.0.0.1:5000/tts'
    try:
        response = requests.get(url)
        return response.status_code == 200
    except requests.RequestException:
        return False

def start_backend_service():
    # 设置工作目录
    work_dir = os.path.join(os.getcwd(), 'GPT-SoVITS-Inference')
    
    # 构建命令
    cmd = f'start cmd /K "chcp 65001 && cd /d {work_dir} && runtime\\python.exe pure_api.py"'
    
    # 启动进程
    process = subprocess.Popen(
        cmd,
        shell=True,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    
    print("启动SoVits服务中，请稍等...") 
    time.sleep(10)  # 等10s
    
    for _ in range(5):  # 每隔5s ping一次，一共ping 5次
        if ping_tts_service():
            print("服务已启动")
            return process  # 返回进程对象
        time.sleep(5)

    raise Exception("服务在30秒内未启动")

def send_tts_request(character=DUBBNING_CHARACTER, text='', speed=1, batch_size=1, save_as='output.wav', cut_last=0):
    url = 'http://127.0.0.1:5000/tts'
    encoded_text = urllib.parse.quote(text)
    payload = {'character': character, 'text': encoded_text, 'speed': speed, 'batch_size': batch_size}
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        if 'audio/wav' in response.headers.get('Content-Type', ''):
            temp_file = 'temp_output.wav'
            with open(temp_file, 'wb') as f:
                f.write(response.content)
            
            y, sr = librosa.load(temp_file, sr=None)
            target_length = len(y) - int(cut_last * sr)  # 计算要保留的音频长度
            y_trimmed = y[:target_length]  # 切片音频
            sf.write(save_as, y_trimmed, sr)  # 保存处理后的音频
            os.remove(temp_file)  # 删除临时文件
            
            return f"处理后的音频已保存为 {save_as}"
        else:
            return response.text
    except requests.RequestException as e:
        return f"发送请求时出错: {str(e)}"
    except Exception as e:
        return f"处理音频时出错: {str(e)}"

def check_wav_duration(file_path):
    try:
        audio_info = sf.info(file_path)
        return audio_info.duration  # 返回文件的时长
    except Exception as e:
        raise Exception(f"Error checking duration: {str(e)}")

def parse_srt_time(time_str):
    hours, minutes, seconds = time_str.strip().split(':')
    seconds, milliseconds = seconds.split(',')
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000

def generate_audio(character, text, target_duration, save_as, number):
    """
    生成音频并选择最接近目标时长的版本
    """
    speeds = [0.9, 1.0, 1.15, 1.3]
    results = []
    os.makedirs('output/audio/tmp', exist_ok=True)

    for speed in speeds:
        for i in range(3):
            temp_filename = f"output/audio/tmp/{number}_temp_{speed}_{i+1}.wav"
            send_tts_request(character, text, speed, 1, temp_filename)
            duration = check_wav_duration(temp_filename)
            
            if not target_duration <= MIN_SUBTITLE_DURATION:
                # 早停机制 95%
                if 0.95 * target_duration <= duration <= target_duration:
                    os.rename(temp_filename, save_as)
                    print(f"✅ {number} 提前选中的音频: {save_as}, 时长: {duration:.2f}秒，要求的时长: {target_duration:.2f}秒, 此时的速度: {speed}")
                    for filename, _ in results:
                        os.remove(filename)
                    return
                
            results.append((temp_filename, duration))

    results_with_diff = [(filename, duration, abs(duration - target_duration)) for filename, duration in results]
    results_with_diff.sort(key=lambda x: x[2])
    results_with_diff = [r for r in results_with_diff if r[1] <= target_duration]
    
    if target_duration <= MIN_SUBTITLE_DURATION:
        selected = results_with_diff[len(results_with_diff) // 2]
    else:
        selected = next((r for r in results_with_diff if r[1] <= target_duration), results_with_diff[0])

    os.rename(selected[0], save_as)

    for filename, _ in results:
        if filename != selected[0]:
            os.remove(filename)

    print(f"✅ {number} 选中的音频: {save_as}, 时长: {selected[1]:.2f}秒，要求的时长: {target_duration:.2f}秒")

def process_sovits_tasks():
    process = None
    if not ping_tts_service():
        process = start_backend_service()

    tasks_df = pd.read_excel("output/audio/sovits_tasks.xlsx")
    error_tasks = []
    for _, row in tqdm(tasks_df.iterrows(), total=len(tasks_df), desc='处理任务'): 
        number = row['number']
        duration = float(row['duration'])
        text = row['text']
        output_file = f'output/audio/{number}.wav'

        if os.path.exists(output_file):
            print(f"文件 {output_file} 已存在,跳过处理")
            continue
        
        try:
            generate_audio(DUBBNING_CHARACTER, text, duration, output_file, number)
        except Exception as e:
            try:
                print(f"任务 {number} 处理出错: {str(e)}，尝试精简字幕...")
                prompt = get_subtitle_trim_prompt(text, duration, fierce_mode = True)
                response = ask_gpt(prompt, model=step9_trim_model, response_json=True, log_title='sovits_trim')
                text = response['trans_text_processed']
                print(f"精简前的字幕：{row['text']}\n精简后的字幕: {text}")
                generate_audio(DUBBNING_CHARACTER, text, duration, output_file, number)
            except Exception as e:
                error_tasks.append(number)
                print(f"任务 {number} 处理出错: {str(e)}")

    if error_tasks:
        error_msg = f"以下任务处理出错: {', '.join(map(str, error_tasks))}，请检查 output/audio/sovits_tasks.xlsx 中的对应内容并修改。"
        print(error_msg)
        raise Exception(error_msg)
    
    print("任务处理完成，服务已关闭")

if __name__ == "__main__":
    process_sovits_tasks()