import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import json
import concurrent.futures
from core.translate_once import translate_lines
from core.step4_1_summarize import search_things_to_note_in_prompt
from core.step8_gen_audio_task import check_len_then_trim
from core.step6_generate_final_timeline import align_timestamp
from core.config_utils import load_key
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# Function to split text into chunks
def split_chunks_by_chars(chunk_size=600, max_i=12): 
    """Split text into chunks based on character count, return a list of multi-line text chunks"""
    with open("output/log/sentence_splitbymeaning.txt", "r", encoding="utf-8") as file:
        sentences = file.read().strip().split('\n')

    chunks = []
    chunk = ''
    sentence_count = 0
    for sentence in sentences:
        if len(chunk) + len(sentence + '\n') > chunk_size or sentence_count == max_i:
            chunks.append(chunk.strip())
            chunk = sentence + '\n'
            sentence_count = 1
        else:
            chunk += sentence + '\n'
            sentence_count += 1
    chunks.append(chunk.strip())
    return chunks

# Get context from surrounding chunks
def get_previous_content(chunks, chunk_index):
    return None if chunk_index == 0 else chunks[chunk_index - 1].split('\n')[-3:] # Get last 3 lines
def get_after_content(chunks, chunk_index):
    return None if chunk_index == len(chunks) - 1 else chunks[chunk_index + 1].split('\n')[:2] # Get first 2 lines

# 🔍 Translate a single chunk
def translate_chunk(chunk, chunks, theme_prompt, i):
    things_to_note_prompt = search_things_to_note_in_prompt(chunk)
    previous_content_prompt = get_previous_content(chunks, i)
    after_content_prompt = get_after_content(chunks, i)
    translation, english_result = translate_lines(chunk, previous_content_prompt, after_content_prompt, things_to_note_prompt, theme_prompt, i)
    return i, english_result, translation

# 🚀 Main function to translate all chunks
def translate_all():
    # Check if the file exists
    if os.path.exists("output/log/translation_results.xlsx"):
        console.print(Panel("🚨 File `translation_results.xlsx` already exists, skipping TRANSLATE ALL.", title="Warning", border_style="yellow"))
        return
    
    console.print("[bold green]Start Translating All...[/bold green]")
    if 'sonnet' in load_key("api.model"):
        chunks = split_chunks_by_chars()
    else:
        console.print("[yellow]🚨 Not using sonnet, using smaller chunk size and max_i to avoid OOM[/yellow]")
        chunks = split_chunks_by_chars(chunk_size=500, max_i=10)
    with open('output/log/terminology.json', 'r', encoding='utf-8') as file:
        theme_prompt = json.load(file).get('theme')

    # 🔄 Use concurrent execution for translation
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("[cyan]Translating chunks...", total=len(chunks))
        with concurrent.futures.ThreadPoolExecutor(max_workers=load_key("max_workers")) as executor:
            futures = []
            for i, chunk in enumerate(chunks):
                future = executor.submit(translate_chunk, chunk, chunks, theme_prompt, i)
                futures.append(future)

            results = []
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
                progress.update(task, advance=1)

    results.sort(key=lambda x: x[0])  # Sort results based on original order
    
    # 💾 Save results to lists and Excel file
    src_text, trans_text = [], []
    for _, chunk, translation in results:
        src_text.extend(chunk.split('\n'))
        trans_text.extend(translation.split('\n'))
    
    # Trim long translation text
    df_text = pd.read_excel('output/log/cleaned_chunks.xlsx')
    df_text['text'] = df_text['text'].str.strip('"').str.strip()
    df_translate = pd.DataFrame({'Source': src_text, 'Translation': trans_text})
    subtitle_output_configs = [('trans_subs_for_audio.srt', ['Translation'])]
    df_time = align_timestamp(df_text, df_translate, subtitle_output_configs, output_dir=None, for_display=False)
    console.print(df_time)
    # apply check_len_then_trim to df_time['Translation'], only when duration > MIN_TRIM_DURATION.
    df_time['Translation'] = df_time.apply(lambda x: check_len_then_trim(x['Translation'], x['duration']) if x['duration'] > load_key("min_trim_duration") else x['Translation'], axis=1)
    console.print(df_time)
    
    df_time.to_excel("output/log/translation_results.xlsx", index=False)
    console.print("[bold green]✅ Translation completed and results saved.[/bold green]")

if __name__ == '__main__':
    translate_all()