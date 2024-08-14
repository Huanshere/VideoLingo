import sys, os
import pandas as pd
from typing import List, Tuple
import concurrent.futures
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.step3_2_splitbymeaning import split_sentence
from core.ask_gpt import ask_gpt, step5_align_model
from core.prompts_storage import get_align_prompt
from config import TARGET_LANGUAGE, MAX_ENGLISH_LENGTH, MAX_TARGET_LANGUAGE_LENGTH

# TODO you can modify your own function here
def calc_len(text: str) -> float:
    # 🇨🇳 characters are counted as 1, others are counted as 0.75
    if not isinstance(text, str):
        print(f"🚨 Warning: calc_len received a non-string input: {text}")
        text = str(text)
    if '中文' in TARGET_LANGUAGE or 'cn' in TARGET_LANGUAGE: 
        return sum(1 if ord(char) > 127 else 0.75 for char in text)
    else:
        return len(text)

def align_subs(en_sub: str, tr_sub: str, en_part: str) -> Tuple[List[str], List[str]]:
    align_prompt = get_align_prompt(en_sub, tr_sub, en_part, target_language=TARGET_LANGUAGE)
    
    parsed = ask_gpt(align_prompt, model=step5_align_model, response_json=True, log_title='align_subs')

    best = int(parsed['best_way'])
    align_data = parsed[f'align_way_{best}']
    
    en_parts = en_part.split('\n')
    tr_parts = [item[f'target_part_{i+1}'].strip() for i, item in enumerate(align_data)]
    
    print(f"🔗 Aligned parts:\nSRC_LANG:    {en_parts}\nTARGET_LANG: {tr_parts}\n================")
    return en_parts, tr_parts

def split_align_subs(en_lines: List[str], tr_lines: List[str], max_en_len=80, max_tr_len=30, max_retry=5) -> Tuple[List[str], List[str]]:
    for attempt in range(max_retry):
        print(f"🔄 Splitting attempt {attempt + 1}")
        to_split = []
        
        for i, (en, tr) in enumerate(zip(en_lines, tr_lines)):
            if len(en) > max_en_len or calc_len(tr) > max_tr_len:
                to_split.append(i)
                print(f"📏 Line {i} needs splitting:\nSRC_LANG:    {en}\nTARGET_LANG: {tr}\n================")
        
        def process(i):
            split_en = split_sentence(en_lines[i], num_parts=2).strip()
            en_lines[i], tr_lines[i] = align_subs(en_lines[i], tr_lines[i], split_en)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            executor.map(process, to_split)
        
        # Flatten `en_lines` and `tr_lines`
        en_lines = [item for sublist in en_lines for item in (sublist if isinstance(sublist, list) else [sublist])]
        tr_lines = [item for sublist in tr_lines for item in (sublist if isinstance(sublist, list) else [sublist])]
        
        if all(len(en) <= max_en_len for en in en_lines) and all(calc_len(tr) <= max_tr_len for tr in tr_lines):
            break
    
    return en_lines, tr_lines

def split_for_sub_main():
    print('🚀 Starting subtitle splitting process...')
    df = pd.read_excel("output/log/translation_results.xlsx")
    
    en_lines = df['English'].tolist()
    tr_lines = df['Translation'].tolist()
    
    en_lines, tr_lines = split_align_subs(en_lines, tr_lines, MAX_ENGLISH_LENGTH, MAX_TARGET_LANGUAGE_LENGTH)
    
    pd.DataFrame({'English': en_lines, 'Translation': tr_lines}).to_excel("output/log/translation_results_for_subtitles.xlsx", index=False)
    print('✅ Subtitle splitting process completed!')

if __name__ == '__main__':
    split_for_sub_main()