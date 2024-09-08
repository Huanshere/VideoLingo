import os
import pandas as pd
from tqdm import tqdm
import soundfile as sf
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.prompts_storage import get_subtitle_trim_prompt
from core.ask_gpt import ask_gpt
from third_party.GPT_SoVITS_Inference.SoVITS_for_videolingo import init_model, tts_function, unload_model

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

def generate_audio(text, character, target_duration, save_as, number):
    """
    生成音频并选择最接近目标时长的版本
    """
    from config import MIN_SUBTITLE_DURATION
    speeds = [1.0, 1.15, 1.3]
    results = []
    os.makedirs('output/audio/tmp', exist_ok=True)

    for speed in speeds:
        for i in range(3):
            temp_filename = f"output/audio/tmp/{number}_temp_{speed}_{i+1}.wav"
            send_tts_request(text, character, speed, temp_filename)
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

def init_sovits_model():
    now_path = os.getcwd()
    # 切换目录到 GPT_SoVITS_Inference再回来
    os.chdir("GPT_SoVITS_Inference")
    init_model()
    os.chdir(now_path)

def send_tts_request(text, character, speed=1.0, save_path='output/audio/temp.wav'):
    now_path = os.getcwd()
    save_path = os.path.join(now_path, save_path)
    os.chdir("GPT_SoVITS_Inference")
    audio_file = tts_function(text, character=character, speed=speed, save_path=save_path)
    os.chdir(now_path)
    return audio_file

def process_sovits_tasks():
    init_sovits_model()

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
        
        from config import step9_trim_model, DUBBING_CHARACTER
        for attempt in range(3): # 尝试三次
            try:
                generate_audio(text, DUBBING_CHARACTER, duration, output_file, number)
                break  # 如果生成音频成功，跳出循环
            except Exception as e:
                if attempt < 2:  # 第一次和第二次尝试
                    print(f"任务 {number} 处理出错: {str(e)}，尝试第{attempt + 1}次精简字幕...")
                    prompt = get_subtitle_trim_prompt(text, duration, fierce_mode=True)
                    response = ask_gpt(prompt, model=step9_trim_model, response_json=True, log_title='sovits_trim')
                    text = response['trans_text_processed']
                    print(f"第{attempt + 1}次精简前的字幕：{row['text']}\n第{attempt + 1}次精简后的字幕: {text}")
                else:  # 第三次尝试失败
                    error_tasks.append(number)
                    print(f"任务 {number} 处理出错: {str(e)}")
                    break  # 跳出循环，处理下一个任务

    if error_tasks:
        error_msg = f"以下任务处理出错: {', '.join(map(str, error_tasks))}，请检查 output/audio/sovits_tasks.xlsx 中的对应内容并修改。"
        print(error_msg)
        raise Exception(error_msg)
    
    unload_model()
    print("任务处理完成，服务已关闭")

if __name__ == "__main__":
    process_sovits_tasks()