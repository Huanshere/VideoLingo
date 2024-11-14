import pandas as pd
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config_utils import load_key
from core.all_whisper_methods.whisperX_utils import get_audio_duration
from core.step8_1_gen_audio_task import time_diff_seconds
import datetime
import re
from core.all_tts_functions.estimate_duration import init_estimator, estimate_duration

INPUT_EXCEL = "output/audio/tts_tasks.xlsx"
OUTPUT_EXCEL = "output/audio/tts_tasks.xlsx"
TRANSCRIPT_FILE = "output/trans.srt"
MAX_MERGE_COUNT = 5
AUDIO_FILE = 'output/audio/raw.mp3'
ESTIMATOR = None

def calc_if_too_fast(est_dur, tol_dur, duration, tolerance):
    accept = load_key("speed_factor.accept") # 接受的最大变速
    if est_dur / accept > tol_dur:  # 即使最大变速也无法适应
        return 2
    elif est_dur > tol_dur:  # 需要变速但是在接受范围内
        return 1
    elif est_dur < duration - tolerance:  # 语速过慢
        return -1
    else:  # 语速正常
        return 0

def merge_rows(df, start_idx, merge_count):
    """合并多行并计算累计值"""
    merged = {
        'est_dur': df.iloc[start_idx]['est_dur'],
        'tol_dur': df.iloc[start_idx]['tol_dur'],
        'duration': df.iloc[start_idx]['duration']
    }
    
    while merge_count < MAX_MERGE_COUNT and (start_idx + merge_count) < len(df):
        next_row = df.iloc[start_idx + merge_count]
        merged['est_dur'] += next_row['est_dur']
        merged['tol_dur'] += next_row['tol_dur']
        merged['duration'] += next_row['duration']
        
        speed_flag = calc_if_too_fast(
            merged['est_dur'],
            merged['tol_dur'],
            merged['duration'],
            df.iloc[start_idx + merge_count]['tolerance']
        )
        
        if speed_flag <= 0 or merge_count == 2:
            df.at[start_idx + merge_count, 'cut_off'] = 1
            return merge_count + 1
        
        merge_count += 1
    
    # 如果没找到合适的合并点
    if merge_count >= MAX_MERGE_COUNT or (start_idx + merge_count) >= len(df):
        df.at[start_idx + merge_count - 1, 'cut_off'] = 1
    return merge_count

def analyze_subtitle_timing_and_speed(df):
    """计算每行字幕与下一行字幕之间的时间间隔"""
    global ESTIMATOR
    if ESTIMATOR is None:
        ESTIMATOR = init_estimator()
    TOLERANCE = load_key("tolerance")
    whole_dur = get_audio_duration(AUDIO_FILE)
    df['gap'] = 0.0  # 初始化gap列
    for i in range(len(df) - 1):
        current_end = datetime.datetime.strptime(df.loc[i, 'end_time'], '%H:%M:%S.%f').time()
        next_start = datetime.datetime.strptime(df.loc[i + 1, 'start_time'], '%H:%M:%S.%f').time()
        df.loc[i, 'gap'] = time_diff_seconds(current_end, next_start, datetime.date.today())
    
    # 设置最后一行的gap
    last_end = datetime.datetime.strptime(df.iloc[-1]['end_time'], '%H:%M:%S.%f').time()
    last_end_seconds = (last_end.hour * 3600 + last_end.minute * 60 + 
                       last_end.second + last_end.microsecond / 1000000)
    df.iloc[-1, df.columns.get_loc('gap')] = whole_dur - last_end_seconds
    
    df['tolerance'] = df['gap'].apply(lambda x: TOLERANCE if x > TOLERANCE else x)
    df['tol_dur'] = df['duration'] + df['tolerance']
    df['est_dur'] = df.apply(lambda x: estimate_duration(x['text'], ESTIMATOR), axis=1)

    ## 计算速度指标
    accept = load_key("speed_factor.accept") # 接受的最大变速
    def calc_if_too_fast(row):
        est_dur = row['est_dur']
        tol_dur = row['tol_dur']
        duration = row['duration']
        tolerance = row['tolerance']
        
        if est_dur / accept > tol_dur:  # 即使最大变速也无法适应
            return 2
        elif est_dur > tol_dur:  # 需要变速但是在接受范围内
            return 1
        elif est_dur < duration - tolerance:  # 语速过慢
            return -1
        else:  # 语速正常
            return 0
    
    df['if_too_fast'] = df.apply(calc_if_too_fast, axis=1)
    return df

def process_cutoffs(df):
    df['cut_off'] = 0  # 初始化cut_off列
    df.loc[df['gap'] >= load_key("tolerance"), 'cut_off'] = 1  # 当gap大于TOLERANCE时设置为1
    idx = 0
    while idx < len(df):
        # 处理已标记的切分点
        if df.iloc[idx]['cut_off'] == 1:
            if df.iloc[idx]['if_too_fast'] == 2:
                print(f"警告: 行 {idx} 语速过快且无法通过变速解决")
            idx += 1
            continue

        # 处理最后一行
        if idx + 1 >= len(df):
            df.at[idx, 'cut_off'] = 1
            break

        # 处理正常或慢速的行
        if df.iloc[idx]['if_too_fast'] <= 0:
            if df.iloc[idx + 1]['if_too_fast'] <= 0:
                df.at[idx, 'cut_off'] = 1
                idx += 1
            else:
                idx += merge_rows(df, idx, 1)
        # 处理快速的行
        else:
            idx += merge_rows(df, idx, 1)
    
    return df

def main():
    # 读取Excel文件
    df = pd.read_excel(INPUT_EXCEL)
    df = analyze_subtitle_timing_and_speed(df)
    df = process_cutoffs(df)

    # 读取字幕文件
    content = open(TRANSCRIPT_FILE, "r", encoding="utf-8").read()

    # 处理字幕内容
    content_lines = []
    for block in content.strip().split('\n\n'):
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if len(lines) >= 3:
            text = ' '.join(lines[2:])
            # 清理文本
            text = re.sub(r'\([^)]*\)|（[^）]*）', '', text).strip().replace('-', '')
            content_lines.append(text)

    # 匹配处理
    df['lines'] = None
    last_idx = 0

    for idx, row in df.iterrows():
        target = row['text'].replace(' ', '')
        matches = []
        current = ''
        
        for i in range(last_idx, len(content_lines)):
            line = content_lines[i].replace(' ', '')
            current += line
            matches.append(content_lines[i])
            
            if current == target:
                df.at[idx, 'lines'] = matches
                last_idx = i + 1
                break
        else:  # 如果没有找到匹配
            raise ValueError(f"\n匹配失败 - 行 {idx}:\n目标: '{target}'\n当前: '{current}'")

    # 保存结果
    df.to_excel(OUTPUT_EXCEL, index=False)
    print("匹配完成！")

if __name__ == "__main__":
    main()