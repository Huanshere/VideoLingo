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
from core.config_utils import load_key  

console = Console()
speed_factor = load_key("speed_factor")

TRANS_SUBS_FOR_AUDIO_FILE = 'output/audio/trans_subs_for_audio.srt'
SRC_SUBS_FOR_AUDIO_FILE = 'output/audio/src_subs_for_audio.srt'
SOVITS_TASKS_FILE = 'output/audio/sovits_tasks.xlsx'

def check_len_then_trim(text, duration):
    multiplier = speed_factor['normal'] * speed_factor['max']
    # Define speech speed: characters/second or words/second, punctuation/second
    speed_zh_ja = 4 * multiplier  # Chinese and Japanese characters per second
    speed_en_and_others = 5 * multiplier   # Words per second for English and other languages
    speed_punctuation = 4 * multiplier   # Punctuation marks per second
    
    # Count characters, words, and punctuation for each language
    chinese_japanese_chars = len(re.findall(r'[\u4e00-\u9fff\u3040-\u30ff\u3400-\u4dbf\uf900-\ufaff\uff66-\uff9f]', text))
    en_and_others_words = len(re.findall(r'\b[a-zA-ZàâçéèêëîïôûùüÿñæœáéíóúüñÁÉÍÓÚÜÑàèéìíîòóùúÀÈÉÌÍÎÒÓÙÚäöüßÄÖÜа-яА-Я]+\b', text))
    punctuation_count = len(re.findall(r'[,.!?;:，。！？；：](?=.)', text))
    
    # Estimate duration for each language part and punctuation
    chinese_japanese_duration = chinese_japanese_chars / speed_zh_ja
    en_and_others_duration = en_and_others_words / speed_en_and_others
    punctuation_duration = punctuation_count / speed_punctuation
    
    # Total estimated duration
    estimated_duration = chinese_japanese_duration + en_and_others_duration + punctuation_duration
    
    console.print(f"Subtitle text: {text}, "
                  f"Subtitle info: Chinese/Japanese chars: {chinese_japanese_chars}, "
                  f"English and other language words: {en_and_others_words}, "
                  f"Punctuation marks: {punctuation_count}, "
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
            response = ask_gpt(prompt, response_json=True, log_title='subtitle_trim', valid_def=valid_trim)
            shortened_text = response['result']
        except Exception:
            rprint("[bold red]🚫 AI refused to answer due to sensitivity, so manually remove punctuation[/bold red]")
            shortened_text = re.sub(r'[,.!?;:，。！？；：]', ' ', text).strip()
        rprint(Panel(f"Subtitle before shortening: {original_text}\nSubtitle after shortening: {shortened_text}", title="Subtitle Shortening Result", border_style="green"))
        return shortened_text
    else:
        return text

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
            duration = (datetime.datetime.combine(datetime.date.today(), end_time) - 
                        datetime.datetime.combine(datetime.date.today(), start_time)).total_seconds()
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
    MIN_SUBTITLE_DURATION = load_key("min_subtitle_duration")
    while i < len(df):
        if df.loc[i, 'duration'] < MIN_SUBTITLE_DURATION:
            if i < len(df) - 1 and (datetime.datetime.combine(datetime.date.today(), df.loc[i+1, 'start_time']) - 
                                    datetime.datetime.combine(datetime.date.today(), df.loc[i, 'start_time'])).total_seconds() < MIN_SUBTITLE_DURATION:
                rprint(f"[bold yellow]Merging subtitles {i+1} and {i+2}[/bold yellow]")
                df.loc[i, 'text'] += ' ' + df.loc[i+1, 'text']
                df.loc[i, 'origin'] += ' ' + df.loc[i+1, 'origin']
                df.loc[i, 'end_time'] = df.loc[i+1, 'end_time']
                df.loc[i, 'duration'] = (datetime.datetime.combine(datetime.date.today(), df.loc[i, 'end_time']) - 
                                        datetime.datetime.combine(datetime.date.today(), df.loc[i, 'start_time'])).total_seconds()
                df = df.drop(i+1).reset_index(drop=True)
            else:
                if i < len(df) - 1:  # Not the last audio
                    rprint(f"[bold blue]Extending subtitle {i+1} duration to {MIN_SUBTITLE_DURATION} seconds[/bold blue]")
                    df.loc[i, 'end_time'] = (datetime.datetime.combine(datetime.date.today(), df.loc[i, 'start_time']) + 
                                            datetime.timedelta(seconds=MIN_SUBTITLE_DURATION)).time()
                    df.loc[i, 'duration'] = MIN_SUBTITLE_DURATION
                else:
                    rprint(f"[bold red]The last subtitle {i+1} duration is less than {MIN_SUBTITLE_DURATION} seconds, but not extending[/bold red]")
                i += 1
        else:
            i += 1
    
    df['start_time'] = df['start_time'].apply(lambda x: x.strftime('%H:%M:%S.%f')[:-3])
    df['end_time'] = df['end_time'].apply(lambda x: x.strftime('%H:%M:%S.%f')[:-3])
    
    # check and trim subtitle length, for twice to ensure the subtitle length is within the limit
    for _ in range(2):
        df['text'] = df.apply(lambda x: check_len_then_trim(x['text'], x['duration']), axis=1)

    return df

def gen_audio_task_main():
    if os.path.exists(SOVITS_TASKS_FILE):
        rprint(Panel(f"{SOVITS_TASKS_FILE} already exists, skip.", title="Info", border_style="blue"))
    else:
        df = process_srt()
        console.print(df)
        df.to_excel(SOVITS_TASKS_FILE, index=False)

        rprint(Panel(f"Successfully generated {SOVITS_TASKS_FILE}", title="Success", border_style="green"))

if __name__ == '__main__':
    gen_audio_task_main()