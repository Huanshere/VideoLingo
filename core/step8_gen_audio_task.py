import pandas as pd
import datetime
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import re
from core.ask_gpt import ask_gpt
from core.prompts_storage import get_subtitle_trim_prompt
from rich import print as rprint
from rich.panel import Panel
from rich.console import Console

console = Console()

# TODO: 需要优化，目前只考虑了中英文标点符号，没有考虑其他语言的标点符号
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
    
    # 计算最大允许字符数
    max_chars = int(duration * max_chars_per_second)
    
    console.print(f"字幕信息: 汉字: {chinese_chars}, 英文单词: {english_words}, 数字: {numbers}, 标点符号: {punct_count}, 总长度: {total_length}  [bold green]最大允许长度：{max_chars}[/bold green]")
    
    if total_length > max_chars:
        rprint(Panel(f"字幕长度超过{max_chars}，正在缩短...", title="正在处理", border_style="yellow"))
        original_text = text
        prompt = get_subtitle_trim_prompt(text, duration)
        from config import step9_trim_model
        response = ask_gpt(prompt, model = step9_trim_model,response_json=True, log_title='subtitle_trim')
        shortened_text = response['trans_text_processed']
        rprint(Panel(f"缩短前的字幕：{original_text}\n缩短后的字幕: {shortened_text}", title="字幕缩短结果", border_style="green"))
        return shortened_text
    else:
        return text

def process_srt():
    """处理 srt 文件，生成音频任务"""
    output_dir = 'output/audio'
    trans_subs = os.path.join(output_dir, 'trans_subs_for_audio.srt')

    src_file_path = os.path.join(output_dir, 'src_subs_for_audio.srt')
    
    with open(trans_subs, 'r', encoding='utf-8') as file:
        content = file.read()
    
    with open(src_file_path, 'r', encoding='utf-8') as src_file:
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
            duration = (datetime.datetime.combine(datetime.date.today(), end_time) - 
                        datetime.datetime.combine(datetime.date.today(), start_time)).total_seconds()
            text = ' '.join(lines[2:])
            # 删除括号内的内容（包括英文和中文括号）
            text = re.sub(r'\([^)]*\)', '', text).strip()
            text = re.sub(r'（[^）]*）', '', text).strip()
            # 删掉 - 字符，可继续补充会导致错误的非法字符
            text = text.replace('-', '')

            # Add the original text from src_subs_for_audio.srt
            origin = src_subtitles.get(number, '')

        except ValueError as e:
            rprint(Panel(f"无法解析字幕块 '{block}'，错误: {str(e)}，跳过此字幕块。", title="错误", border_style="red"))
            continue
        
        subtitles.append({
            'number': number,
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'text': text,
            'origin': origin
        })
    
    df = pd.DataFrame(subtitles)
    
    i = 0
    from config import MIN_SUBTITLE_DURATION
    while i < len(df):
        if df.loc[i, 'duration'] < MIN_SUBTITLE_DURATION:
            if i < len(df) - 1 and (datetime.datetime.combine(datetime.date.today(), df.loc[i+1, 'start_time']) - 
                                    datetime.datetime.combine(datetime.date.today(), df.loc[i, 'start_time'])).total_seconds() < MIN_SUBTITLE_DURATION:
                rprint(f"[bold yellow]合并字幕 {i+1} 和 {i+2}[/bold yellow]")
                df.loc[i, 'text'] += ' ' + df.loc[i+1, 'text']
                df.loc[i, 'origin'] += ' ' + df.loc[i+1, 'origin']
                df.loc[i, 'end_time'] = df.loc[i+1, 'end_time']
                df.loc[i, 'duration'] = (datetime.datetime.combine(datetime.date.today(), df.loc[i, 'end_time']) - 
                                        datetime.datetime.combine(datetime.date.today(), df.loc[i, 'start_time'])).total_seconds()
                df = df.drop(i+1).reset_index(drop=True)
            else:
                if i < len(df) - 1:  # 不是最后一条音频
                    rprint(f"[bold blue]延长字幕 {i+1} 的持续时间到{MIN_SUBTITLE_DURATION}秒[/bold blue]")
                    df.loc[i, 'end_time'] = (datetime.datetime.combine(datetime.date.today(), df.loc[i, 'start_time']) + 
                                            datetime.timedelta(seconds=MIN_SUBTITLE_DURATION)).time()
                    df.loc[i, 'duration'] = MIN_SUBTITLE_DURATION
                else:
                    rprint(f"[bold red]最后一条字幕 {i+1} 的持续时间小于{MIN_SUBTITLE_DURATION}秒，但不进行延长[/bold red]")
                i += 1
        else:
            i += 1
    
    df['start_time'] = df['start_time'].apply(lambda x: x.strftime('%H:%M:%S.%f')[:-3])
    df['end_time'] = df['end_time'].apply(lambda x: x.strftime('%H:%M:%S.%f')[:-3])
    
    # 检查字幕长度 # 处理两次以确保字幕长度不超过限制
    df['text'] = df.apply(lambda x: check(x['text'], x['duration']), axis=1)
    df['text'] = df.apply(lambda x: check(x['text'], x['duration']), axis=1)

    return df

def gen_audio_task_main():
    output_dir = 'output/audio'
    tasks_file = os.path.join(output_dir, 'sovits_tasks.xlsx')
    
    if os.path.exists(tasks_file):
        rprint(Panel(f"{tasks_file} already exists, skip.", title="信息", border_style="blue"))
    else:
        df = process_srt()
        console.print(df)
        df.to_excel(tasks_file, index=False)

        rprint(Panel(f"Successfully generated {tasks_file}", title="成功", border_style="green"))

if __name__ == '__main__':
    gen_audio_task_main()