import pandas as pd
import datetime
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MIN_SUBTITLE_DURATION, step9_trim_model
import re
from core.ask_gpt import ask_gpt
from core.prompts_storage import get_subtitle_trim_prompt


def check(text, duration, max_chars_per_second=8):
    # 定义标点符号列表
    punctuations = ',，。！？：；"（）《》【】'
    
    # 分别计算汉字、英文单词、数字和标点符号的数量
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
    numbers = len(re.findall(r'\d+', text))
    punct_count = sum(text.count(p) for p in punctuations)
    
    # 计算总长度：汉字1个长度，英文单词2个长度，数字1个长度，标点符号4个长度
    total_length = chinese_chars + english_words * 2 + numbers + punct_count * 4
    print(f"字幕长度：{total_length}(汉字：{chinese_chars}，英文单词：{english_words}，数字：{numbers}，标点符号：{punct_count})")
    
    # 计算最大允许字符数
    max_chars = int(duration * max_chars_per_second)
    print(f"最大允许长度：{max_chars}")
    
    if total_length > max_chars:
        print(f"字幕长度超过{max_chars}，需要缩短。")
        original_text = text
        prompt = get_subtitle_trim_prompt(text, duration)
        response = ask_gpt(prompt, model = step9_trim_model,response_json=True, log_title='subtitle_trim')
        shortened_text = response['trans_text_processed']
        print(f"缩短前的字幕：{original_text}\n缩短后的字幕: {shortened_text}")
        return shortened_text
    else:
        return text

def process_srt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    subtitles = []
    for block in content.strip().split('\n\n'):
        lines = block.split('\n')
        if len(lines) < 2:
            continue
        
        try:
            number = int(lines[0].strip())
            start_time, end_time = lines[1].split(' --> ')
            start_time = datetime.datetime.strptime(start_time, '%H:%M:%S,%f').time()
            end_time = datetime.datetime.strptime(end_time, '%H:%M:%S,%f').time()
            duration = (datetime.datetime.combine(datetime.date.today(), end_time) - 
                        datetime.datetime.combine(datetime.date.today(), start_time)).total_seconds()
            text = ' '.join(lines[2:])
            # 删除括号内的内容（包括英文和中文括号）
            text = re.sub(r'\([^)]*\)', '', text).strip()
            text = re.sub(r'（[^）]*）', '', text).strip()
            # 删掉 - 字符，可继续补充会导致错误的非法字符
            text = text.replace('-', '')

        except ValueError:
            print(f"警告：无法解析字幕块 '{block}'，跳过此字幕块。")
            continue
        
        subtitles.append({
            'number': number,
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'text': text
        })
    
    df = pd.DataFrame(subtitles)
    
    i = 0
    while i < len(df):
        if df.loc[i, 'duration'] < MIN_SUBTITLE_DURATION:
            if i < len(df) - 1 and (datetime.datetime.combine(datetime.date.today(), df.loc[i+1, 'start_time']) - 
                                    datetime.datetime.combine(datetime.date.today(), df.loc[i, 'start_time'])).total_seconds() < MIN_SUBTITLE_DURATION:
                print(f"合并字幕 {i+1} 和 {i+2}")
                df.loc[i, 'text'] += ', ' + df.loc[i+1, 'text']
                df.loc[i, 'end_time'] = df.loc[i+1, 'end_time']
                df.loc[i, 'duration'] = (datetime.datetime.combine(datetime.date.today(), df.loc[i, 'end_time']) - 
                                         datetime.datetime.combine(datetime.date.today(), df.loc[i, 'start_time'])).total_seconds()
                df = df.drop(i+1).reset_index(drop=True)
            else:
                print(f"延长字幕 {i+1} 的持续时间到{MIN_SUBTITLE_DURATION}秒")
                df.loc[i, 'end_time'] = (datetime.datetime.combine(datetime.date.today(), df.loc[i, 'start_time']) + 
                                         datetime.timedelta(seconds=MIN_SUBTITLE_DURATION)).time()
                df.loc[i, 'duration'] = MIN_SUBTITLE_DURATION
                i += 1
        else:
            i += 1
    
    df['start_time'] = df['start_time'].apply(lambda x: x.strftime('%H:%M:%S.%f')[:-3])
    df['end_time'] = df['end_time'].apply(lambda x: x.strftime('%H:%M:%S.%f')[:-3])
    
    # 检查字幕长度 # 处理两次以确保字幕长度不超过限制
    df['text'] = df.apply(lambda x: check(x['text'], x['duration']), axis=1)
    df['text'] = df.apply(lambda x: check(x['text'], x['duration']), axis=1)

    return df

def step9_main():
    # skip if the file
    if os.path.exists(r'output\audio\sovits_tasks.xlsx'):
        print(r"output\audio\sovits_tasks.xlsx already exists, skip.")
    else:
        df = process_srt(r'output\audio\translated_subtitles_for_audio.srt')
        print(df)
        df.to_excel(r'output\audio\sovits_tasks.xlsx', index=False)

if __name__ == '__main__':
    step9_main()