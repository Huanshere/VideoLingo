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
    
    def _ts_to_seconds(ts):
        if isinstance(ts, (int, float)):
            return float(ts)
        if isinstance(ts, datetime.time):
            return ts.hour * 3600 + ts.minute * 60 + ts.second + ts.microsecond / 1000000
        return pd.to_timedelta(ts).total_seconds()
    
    df_tts_copy = df_tts.copy()
    
    # time to seconds
    df_tts_copy["start_sec"] = df_tts_copy["start_time"].map(_ts_to_seconds)
    df_tts_copy["end_sec"] = df_tts_copy["end_time"].map(_ts_to_seconds)
    df_word["start_sec"] = df_word["start"].map(_ts_to_seconds)
    df_word["end_sec"] = df_word["end"].map(_ts_to_seconds)
    
    # pre-assign speaker column
    speakers = []
    
    # set tolerance value (seconds)
    tolerance = 0.2
    
    for _, row in df_tts_copy.iterrows():
        s_start = row["start_sec"] - tolerance
        s_end = row["end_sec"] + tolerance
        
        # find words that overlap with the current subtitle time range
        overlapping_words = df_word[(df_word["start_sec"] < s_end) & (df_word["end_sec"] > s_start)]
        
        if overlapping_words.empty:
            speakers.append(None)
            continue
        
        # count the contribution of each speaker
        speaker_counts = overlapping_words.groupby("speaker").size()
        
        # select the speaker with the most contributions
        speakers.append(speaker_counts.idxmax())

    # add speaker information to the original DataFrame
    df_tts["speaker"] = speakers
    
    # print the assignment result statistics
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
    
    # call function to assign speaker to df
    df = assign_speaker_to_ttstask(df)
    
    i = 0
    MIN_SUB_DUR = load_key("min_subtitle_duration")
    MARGIN = 0.05  # 50 ms margin, prevent sticking to the edge
    
    while i < len(df):
        today = datetime.date.today()
        if df.loc[i, 'duration'] < MIN_SUB_DUR:
            if (i < len(df) - 1 and 
                time_diff_seconds(df.loc[i, 'start_time'], df.loc[i+1, 'start_time'], today) < MIN_SUB_DUR and
                df.loc[i, 'speaker'] == df.loc[i+1, 'speaker']):  # ensure same speaker
                rprint(f"[bold yellow]Merging subtitles {i+1} and {i+2} with same speaker: {df.loc[i, 'speaker']}[/bold yellow]")
                df.loc[i, 'text'] += ' ' + df.loc[i+1, 'text']
                df.loc[i, 'origin'] += ' ' + df.loc[i+1, 'origin']
                df.loc[i, 'end_time'] = df.loc[i+1, 'end_time']
                df.loc[i, 'duration'] = time_diff_seconds(df.loc[i, 'start_time'],df.loc[i, 'end_time'],today)
                df = df.drop(i+1).reset_index(drop=True)
            else:
                # if cannot merge (due to different speakers or other reasons)
                if i < len(df) - 1 and df.loc[i, 'speaker'] != df.loc[i+1, 'speaker']:
                    rprint(f"[bold cyan]Cannot merge subtitle {i+1} with {i+2} due to different speakers: {df.loc[i, 'speaker']} vs {df.loc[i+1, 'speaker']}[/bold cyan]")
                
                # only need to check the next subtitle if it is not the last one
                if i < len(df) - 1:
                    gap = time_diff_seconds(df.loc[i, 'start_time'], df.loc[i+1, 'start_time'], today)
                else:
                    gap = float('inf')
                
                # current subtitle is less than the minimum length, and the gap is large enough to fill
                if df.loc[i, 'duration'] < MIN_SUB_DUR and gap > df.loc[i, 'duration']:
                    # expected new duration
                    target_dur = min(MIN_SUB_DUR, gap - MARGIN)
                    if target_dur > df.loc[i, 'duration']:  # defensive judgment
                        new_end = (datetime.datetime.combine(today, df.loc[i, 'start_time']) + 
                                  datetime.timedelta(seconds=target_dur)).time()
                        df.loc[i, 'end_time'] = new_end
                        df.loc[i, 'duration'] = target_dur
                        rprint(f"[bold blue]Extending subtitle {i+1} duration to {target_dur:.2f} seconds (gap: {gap:.2f}s)[/bold blue]")
                    else:
                        rprint(f"[bold red]Cannot extend subtitle {i+1}: target duration {target_dur:.2f}s not greater than current {df.loc[i, 'duration']:.2f}s[/bold red]")
                else:
                    if i < len(df) - 1:
                        rprint(f"[bold red]Cannot extend subtitle {i+1}: gap to next subtitle ({gap:.2f}s) too small[/bold red]")
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