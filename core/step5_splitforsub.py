import sys, os
import pandas as pd
from typing import List, Tuple
import concurrent.futures
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.step3_2_splitbymeaning import split_sentence
from core.ask_gpt import ask_gpt
from core.prompts_storage import get_align_prompt
from core.config_utils import load_key
from rich.panel import Panel
from rich.console import Console
from rich.table import Table

console = Console()

# ! You can modify your own weights here
# Chinese and Japanese 2.5 characters, Korean 2 characters, Thai 1.5 characters, full-width symbols 2 characters, other English-based and half-width symbols 1 character
def calc_len(text: str) -> float:
    text = str(text) # force convert
    def char_weight(char):
        code = ord(char)
        if 0x4E00 <= code <= 0x9FFF or 0x3040 <= code <= 0x30FF:  # Chinese and Japanese
            return 1.75
        elif 0xAC00 <= code <= 0xD7A3 or 0x1100 <= code <= 0x11FF:  # Korean
            return 1.5
        elif 0x0E00 <= code <= 0x0E7F:  # Thai
            return 1
        elif 0xFF01 <= code <= 0xFF5E:  # full-width symbols
            return 1.75
        else:  # other characters (e.g. English and half-width symbols)
            return 1

    return sum(char_weight(char) for char in text)

def align_subs(src_sub: str, tr_sub: str, src_part: str) -> Tuple[List[str], List[str]]:
    align_prompt = get_align_prompt(src_sub, tr_sub, src_part)
    
    def valid_align(response_data):
        # check if the best is in the response_data
        if 'best' not in response_data:
            return {"status": "error", "message": "Missing required key: `best`"}
        return {"status": "success", "message": "Align completed"}
    parsed = ask_gpt(align_prompt, response_json=True, valid_def=valid_align, log_title='align_subs')

    best = int(parsed['best'])
    align_data = parsed[f'align_{best}']
    
    src_parts = src_part.split('\n')
    tr_parts = [item[f'target_part_{i+1}'].strip() for i, item in enumerate(align_data)]
    
    table = Table(title="🔗 Aligned parts")
    table.add_column("Language", style="cyan")
    table.add_column("Parts", style="magenta")
    table.add_row("SRC_LANG", "\n".join(src_parts))
    table.add_row("TARGET_LANG", "\n".join(tr_parts))
    console.print(table)
    
    return src_parts, tr_parts

def split_align_subs(src_lines: List[str], tr_lines: List[str], max_retry=5) -> Tuple[List[str], List[str]]:
    subtitle_set = load_key("subtitle")
    MAX_SUB_LENGTH = subtitle_set["max_length"]
    TARGET_SUB_MULTIPLIER = subtitle_set["target_multiplier"]
    for attempt in range(max_retry):
        console.print(Panel(f"🔄 Split attempt {attempt + 1}", expand=False))
        to_split = []
        
        for i, (src, tr) in enumerate(zip(src_lines, tr_lines)):
            src, tr = str(src), str(tr)
            if len(src) > MAX_SUB_LENGTH or calc_len(tr) * TARGET_SUB_MULTIPLIER > MAX_SUB_LENGTH:
                to_split.append(i)
                table = Table(title=f"📏 Line {i} needs to be split")
                table.add_column("Type", style="cyan")
                table.add_column("Content", style="magenta")
                table.add_row("Source Line", src)
                table.add_row("Target Line", tr)
                console.print(table)
        
        def process(i):
            split_src = split_sentence(src_lines[i], num_parts=2).strip()
            src_lines[i], tr_lines[i] = align_subs(src_lines[i], tr_lines[i], split_src)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=load_key("max_workers")) as executor:
            executor.map(process, to_split)
        
        # Flatten `src_lines` and `tr_lines`
        src_lines = [item for sublist in src_lines for item in (sublist if isinstance(sublist, list) else [sublist])]
        tr_lines = [item for sublist in tr_lines for item in (sublist if isinstance(sublist, list) else [sublist])]
        
        if all(len(src) <= MAX_SUB_LENGTH for src in src_lines) and all(calc_len(tr) * TARGET_SUB_MULTIPLIER <= MAX_SUB_LENGTH for tr in tr_lines):
            break
    
    return src_lines, tr_lines

def split_for_sub_main():
    if os.path.exists("output/log/translation_results_for_subtitles.xlsx"):
        console.print("[yellow]🚨 File `translation_results_for_subtitles.xlsx` already exists, skipping this step.[/yellow]")
        return

    console.print("[bold green]🚀 Start splitting subtitles...[/bold green]")
    df = pd.read_excel("output/log/translation_results.xlsx")
    src_lines = df['Source'].tolist()
    tr_lines = df['Translation'].tolist()
    src_lines, tr_lines = split_align_subs(src_lines, tr_lines, max_retry=5)
    pd.DataFrame({'Source': src_lines, 'Translation': tr_lines}).to_excel("output/log/translation_results_for_subtitles.xlsx", index=False)
    console.print("[bold green]✅ Subtitles splitting completed![/bold green]")

if __name__ == '__main__':
    split_for_sub_main()
