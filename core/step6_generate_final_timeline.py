import pandas as pd
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from difflib import SequenceMatcher
import re
from config import get_joiner, WHISPER_LANGUAGE
from core.step2_whisper import get_whisper_language
from rich.panel import Panel
from rich.console import Console
from rich.table import Table

console = Console()

def convert_to_srt_format(start_time, end_time):
    """Convert time (in seconds) to the format: hours:minutes:seconds,milliseconds"""
    def seconds_to_hmsm(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        milliseconds = int(seconds * 1000) % 1000
        return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"

    start_srt = seconds_to_hmsm(start_time)
    end_srt = seconds_to_hmsm(end_time)
    return f"{start_srt} --> {end_srt}"

def remove_punctuation(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()

def get_sentence_timestamps(df_words, df_sentences):
    time_stamp_list = []
    word_index = 0
    language = get_whisper_language() if WHISPER_LANGUAGE == 'auto' else WHISPER_LANGUAGE
    joiner = get_joiner(language)

    for idx,sentence in df_sentences['Source'].items():
        sentence = remove_punctuation(sentence.lower())
        best_match = {'score': 0, 'start': 0, 'end': 0, 'word_count': 0}
        decreasing_count = 0
        current_phrase = ""
        start_index = word_index  # record the index of the word where the current sentence starts

        while word_index < len(df_words):
            word = remove_punctuation(df_words['text'][word_index].lower())

            current_phrase += word + joiner

            similarity = SequenceMatcher(None, sentence, current_phrase.strip()).ratio()
            if similarity > best_match['score']:
                best_match = {
                    'score': similarity,
                    'start': df_words['start'][start_index],
                    'end': df_words['end'][word_index],
                    'word_count': word_index - start_index + 1,
                    'phrase': current_phrase
                }
                decreasing_count = 0
            else:
                decreasing_count += 1
            # if 5 consecutive words don't match, break the loop
            if decreasing_count >= 5:
                break
            word_index += 1
        
        #! Originally 0.9, but for very short sentences, a single space can cause a difference of 0.8, so we lower the threshold
        if best_match['score'] >= 0.75:
            time_stamp_list.append((float(best_match['start']), float(best_match['end'])))
            word_index = start_index + best_match['word_count']  # update word_index to the start of the next sentence
        else:
            console.print(Panel(f"[yellow]⚠️ Warning: No match found for the sentence: {sentence}[/yellow]"))
            table = Table(title="Match Details")
            table.add_column("Item", style="cyan")
            table.add_column("Value", style="magenta")
            table.add_row("🔍 Original sentence", repr(sentence))
            table.add_row("🔗 Matched", best_match['phrase'])
            table.add_row("📊 Similarity", f"{best_match['score']:.2f}")
            console.print(table)
            console.print("➖" * 25)
        
        start_index = word_index  # update start_index for the next sentence
    
    return time_stamp_list

def align_timestamp(df_text, df_translate, subtitle_output_configs: list, output_dir: str, for_display: bool = True):
    """Align timestamps and add a new timestamp column to df_translate"""
    df_trans_time = df_translate.copy()

    # Assign an ID to each word in df_text['text'] and create a new DataFrame
    words = df_text['text'].str.split(expand=True).stack().reset_index(level=1, drop=True).reset_index()
    words.columns = ['id', 'word']
    words['id'] = words['id'].astype(int)

    # Process timestamps ⏰
    time_stamp_list = get_sentence_timestamps(df_text, df_translate)
    df_trans_time['timestamp'] = time_stamp_list
    df_trans_time['duration'] = df_trans_time['timestamp'].apply(lambda x: x[1] - x[0])

    # Remove gaps 🕳️
    for i in range(len(df_trans_time)-1):
        delta_time = df_trans_time.loc[i+1, 'timestamp'][0] - df_trans_time.loc[i, 'timestamp'][1]
        if 0 < delta_time < 1:
            df_trans_time.at[i, 'timestamp'] = (df_trans_time.loc[i, 'timestamp'][0], df_trans_time.loc[i+1, 'timestamp'][0])

    # Convert start and end timestamps to SRT format
    df_trans_time['timestamp'] = df_trans_time['timestamp'].apply(lambda x: convert_to_srt_format(x[0], x[1]))

    # Polish subtitles: replace punctuation in Translation if for_display
    if for_display:
        df_trans_time['Translation'] = df_trans_time['Translation'].apply(lambda x: re.sub(r'[，。]', ' ', x).strip())

    # Output subtitles 📜
    def generate_subtitle_string(df, columns):
        return ''.join([f"{i+1}\n{row['timestamp']}\n{row[columns[0]].strip()}\n{row[columns[1]].strip() if len(columns) > 1 else ''}\n\n" for i, row in df.iterrows()]).strip()

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        for filename, columns in subtitle_output_configs:
            subtitle_str = generate_subtitle_string(df_trans_time, columns)
            with open(os.path.join(output_dir, filename), 'w', encoding='utf-8') as f:
                f.write(subtitle_str)
    
    return df_trans_time

def align_timestamp_main():
    df_text = pd.read_excel('output/log/cleaned_chunks.xlsx')
    df_text['text'] = df_text['text'].str.strip('"').str.strip()
    df_translate = pd.read_excel('output/log/translation_results_for_subtitles.xlsx')
    df_translate['Translation'] = df_translate['Translation'].apply(lambda x: str(x).strip('。').strip('，') if pd.notna(x) else '')
    # check if there's empty translation
    empty_rows = df_translate[df_translate['Translation'].str.len() == 0]
    if not empty_rows.empty:
        console.print(Panel("[bold red]🚫 Detected empty translation rows! Please manually check the following rows in `output\log\translation_results_for_subtitles.xlsx` and fill them with appropriate content, then run again:[/bold red]"))
        console.print(empty_rows.index.tolist())
        raise ValueError("Empty translation rows detected")
    subtitle_output_configs = [ 
        ('src_subtitles.srt', ['Source']),
        ('trans_subtitles.srt', ['Translation']),
        ('bilingual_src_trans_subtitles.srt', ['Source', 'Translation']),
        ('bilingual_trans_src_subtitles.srt', ['Translation', 'Source'])
    ]
    align_timestamp(df_text, df_translate, subtitle_output_configs, 'output')
    console.print(Panel("[bold green]🎉📝 Subtitles generation completed! Please check in the `output` folder 👀[/bold green]"))

    # for audio
    df_translate_for_audio = pd.read_excel('output/log/translation_results.xlsx')
    df_translate_for_audio['Translation'] = df_translate_for_audio['Translation'].apply(lambda x: str(x).strip('。').strip('，'))
    if (df_translate_for_audio['Translation'].str.len() == 0).sum() > 0:
        console.print(Panel("[bold red]🚫 Detected empty translation rows! Please manually check the empty rows in `output\log\translation_results.xlsx` and fill them with appropriate content, then run again.[/bold red]"))
        raise ValueError("Empty translation rows detected")
    subtitle_output_configs = [
        ('src_subs_for_audio.srt', ['Source']),
        ('trans_subs_for_audio.srt', ['Translation'])
    ]
    align_timestamp(df_text, df_translate_for_audio, subtitle_output_configs, 'output/audio')
    console.print(Panel("[bold green]🎉📝 Audio subtitles generation completed! Please check in the `output/audio` folder 👀[/bold green]"))
    

if __name__ == '__main__':
    align_timestamp_main()