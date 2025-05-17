import datetime
import re
import pandas as pd
from rich.console import Console
from rich.panel import Panel
from core.prompts import get_subtitle_trim_prompt
from core.tts_backend.estimate_duration import SyllableEstimator
from core.utils import *
from core.utils.models import *

console = Console()
speed_factor = load_key("speed_factor")

TRANS_SUBS_FOR_AUDIO_FILE = 'output/audio/trans_subs_for_audio.srt'
SRC_SUBS_FOR_AUDIO_FILE = 'output/audio/src_subs_for_audio.srt'
ESTIMATOR = None

def check_len_then_trim(text, duration):
    global ESTIMATOR
    if ESTIMATOR is None:
        ESTIMATOR = SyllableEstimator()
    result = ESTIMATOR.estimate(text)
    estimated_duration = result.estimated_seconds / speed_factor['max']
    
    console.print(f"Subtitle text: {text}, "
                  f"[bold green]Estimated reading duration: {estimated_duration:.2f} seconds[/bold green]")

    if estimated_duration > duration:
        rprint(Panel(f"Estimated reading duration {estimated_duration:.2f} seconds exceeds given duration {duration:.2f} seconds, shortening...", title="Processing", border_style="yellow"))
        original_text = text
        prompt = get_subtitle_trim_prompt(text, duration)
        def valid_trim(response):
            if 'result' not in response:
                return {'status': 'error', 'message': 'No result in response'}
            return {'status': 'success', 'message': ''}
        try:    
            response = ask_gpt(prompt, resp_type='json', log_title='sub_trim', valid_def=valid_trim)
            shortened_text = response['result']
        except Exception:
            rprint("[bold red]🚫 AI refused to answer due to sensitivity, so manually remove punctuation[/bold red]")
            shortened_text = re.sub(r'[,.!?;:，。！？；：]', ' ', text).strip()
        rprint(Panel(f"Subtitle before shortening: {original_text}\nSubtitle after shortening: {shortened_text}", title="Subtitle Shortening Result", border_style="green"))
        return shortened_text
    else:
        return text

def time_diff_seconds(t1, t2, base_date):
    """Calculate the difference in seconds between two time objects"""
    dt1 = datetime.datetime.combine(base_date, t1)
    dt2 = datetime.datetime.combine(base_date, t2)
    return (dt2 - dt1).total_seconds()

def assign_speaker_to_ttstask(df_tts):
    """Assign speaker to tts task"""
    df_word = pd.read_excel(_2_CLEANED_CHUNKS)
    
    # ------------
    # 将时间戳转换为秒的辅助函数
    # ------------
    def _ts_to_seconds(ts):
        if isinstance(ts, (int, float)):
            return float(ts)
        if isinstance(ts, datetime.time):
            # 将time对象转换为秒
            return ts.hour * 3600 + ts.minute * 60 + ts.second + ts.microsecond / 1000000
        return pd.to_timedelta(ts).total_seconds()
    
    # 复制DataFrame避免修改原始数据
    df_tts_copy = df_tts.copy()
    
    # 统一时间格式为秒
    df_tts_copy["start_sec"] = df_tts_copy["start_time"].map(_ts_to_seconds)
    df_tts_copy["end_sec"] = df_tts_copy["end_time"].map(_ts_to_seconds)
    df_word["start_sec"] = df_word["start"].map(_ts_to_seconds)
    df_word["end_sec"] = df_word["end"].map(_ts_to_seconds)
    
    # 预分配speaker列
    speakers = []
    
    # 设置容差值（秒）
    tolerance = 0.2
    
    for _, row in df_tts_copy.iterrows():
        s_start = row["start_sec"] - tolerance
        s_end = row["end_sec"] + tolerance
        
        # 找出与当前字幕时间段有交集的词
        overlapping_words = df_word[(df_word["start_sec"] < s_end) & (df_word["end_sec"] > s_start)]
        
        if overlapping_words.empty:
            speakers.append(None)
            continue
        
        # 按词数统计每个speaker的贡献
        speaker_counts = overlapping_words.groupby("speaker").size()
        
        # 选择出现次数最多的speaker
        speakers.append(speaker_counts.idxmax())
    
    # 将speaker信息添加到原始DataFrame
    df_tts["speaker"] = speakers
    
    # 打印分配结果统计
    console.print(f"[bold green]Speaker assignment complete: {len([s for s in speakers if s is not None])}/{len(speakers)} subtitles assigned[/bold green]")
    
    return df_tts

def process_srt():
    """Process srt file, generate audio tasks"""
    with open(TRANS_SUBS_FOR_AUDIO_FILE, 'r', encoding='utf-8') as file:
        content = file.read()
    with open(SRC_SUBS_FOR_AUDIO_FILE, 'r', encoding='utf-8') as src_file:
        src_content = src_file.read()
    
    subtitles = []
    src_subtitles = {}
    
    for block in src_content.strip().split('\n\n'):
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if len(lines) < 3:
            continue
        
        number = int(lines[0])
        src_text = ' '.join(lines[2:])
        src_subtitles[number] = src_text
    
    for block in content.strip().split('\n\n'):
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if len(lines) < 3:
            continue
        
        try:
            number = int(lines[0])
            start_time, end_time = lines[1].split(' --> ')
            start_time = datetime.datetime.strptime(start_time, '%H:%M:%S,%f').time()
            end_time = datetime.datetime.strptime(end_time, '%H:%M:%S,%f').time()
            duration = time_diff_seconds(start_time, end_time, datetime.date.today())
            text = ' '.join(lines[2:])
            # Remove content within parentheses (including English and Chinese parentheses)
            text = re.sub(r'\([^)]*\)', '', text).strip()
            text = re.sub(r'（[^）]*）', '', text).strip()
            # Remove '-' character, can continue to add illegal characters that cause errors
            text = text.replace('-', '')

            # Add the original text from src_subs_for_audio.srt
            origin = src_subtitles.get(number, '')

        except ValueError as e:
            rprint(Panel(f"Unable to parse subtitle block '{block}', error: {str(e)}, skipping this subtitle block.", title="Error", border_style="red"))
            continue
        
        subtitles.append({'number': number, 'start_time': start_time, 'end_time': end_time, 'duration': duration, 'text': text, 'origin': origin})
    
    df = pd.DataFrame(subtitles)
    
    # 调用函数给df的speaker赋值
    df = assign_speaker_to_ttstask(df)
    
    i = 0
    MIN_SUB_DUR = load_key("min_subtitle_duration")
    while i < len(df):
        today = datetime.date.today()
        if df.loc[i, 'duration'] < MIN_SUB_DUR:
            if (i < len(df) - 1 and 
                time_diff_seconds(df.loc[i, 'start_time'], df.loc[i+1, 'start_time'], today) < MIN_SUB_DUR and
                df.loc[i, 'speaker'] == df.loc[i+1, 'speaker']):  # 确保speaker相同
                rprint(f"[bold yellow]Merging subtitles {i+1} and {i+2} with same speaker: {df.loc[i, 'speaker']}[/bold yellow]")
                df.loc[i, 'text'] += ' ' + df.loc[i+1, 'text']
                df.loc[i, 'origin'] += ' ' + df.loc[i+1, 'origin']
                df.loc[i, 'end_time'] = df.loc[i+1, 'end_time']
                df.loc[i, 'duration'] = time_diff_seconds(df.loc[i, 'start_time'],df.loc[i, 'end_time'],today)
                df = df.drop(i+1).reset_index(drop=True)
            else:
                # 如果不能合并（因为speaker不同或其他原因）
                if i < len(df) - 1 and df.loc[i, 'speaker'] != df.loc[i+1, 'speaker']:
                    rprint(f"[bold cyan]Cannot merge subtitle {i+1} with {i+2} due to different speakers: {df.loc[i, 'speaker']} vs {df.loc[i+1, 'speaker']}[/bold cyan]")
                
                if i < len(df) - 1:  # Not the last audio
                    rprint(f"[bold blue]Extending subtitle {i+1} duration to {MIN_SUB_DUR} seconds[/bold blue]")
                    df.loc[i, 'end_time'] = (datetime.datetime.combine(today, df.loc[i, 'start_time']) + 
                                            datetime.timedelta(seconds=MIN_SUB_DUR)).time()
                    df.loc[i, 'duration'] = MIN_SUB_DUR
                else:
                    rprint(f"[bold red]The last subtitle {i+1} duration is less than {MIN_SUB_DUR} seconds, but not extending[/bold red]")
                i += 1
        else:
            i += 1
    
    df['start_time'] = df['start_time'].apply(lambda x: x.strftime('%H:%M:%S.%f')[:-3])
    df['end_time'] = df['end_time'].apply(lambda x: x.strftime('%H:%M:%S.%f')[:-3])

    ##! No longer perform secondary trim
    # check and trim subtitle length, for twice to ensure the subtitle length is within the limit, 允许tolerance
    # df['text'] = df.apply(lambda x: check_len_then_trim(x['text'], x['duration']+x['tolerance']), axis=1)

    return df

@check_file_exists(_8_1_AUDIO_TASK)
def gen_audio_task_main():
    df = process_srt()
    console.print(df)
    df.to_excel(_8_1_AUDIO_TASK, index=False)
    rprint(Panel(f"Successfully generated {_8_1_AUDIO_TASK}", title="Success", border_style="green"))

if __name__ == '__main__':
    gen_audio_task_main()