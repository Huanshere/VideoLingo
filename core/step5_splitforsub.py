import sys, os
import pandas as pd
from typing import List, Tuple
import concurrent.futures
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.step3_2_splitbymeaning import split_sentence
from core.ask_gpt import ask_gpt, step5_align_model
from core.prompts_storage import get_align_prompt

# TODO you can modify your own function here
def calc_len(text: str) -> float:
    from config import TARGET_LANGUAGE
    # 🇨🇳 characters are counted as 1, others are counted as 0.75
    if '中文' in TARGET_LANGUAGE or 'cn' in TARGET_LANGUAGE: 
        return sum(1 if ord(char) > 127 else 0.75 for char in text)
    else:
        return len(text)

def align_subs(src_sub: str, tr_sub: str, src_part: str) -> Tuple[List[str], List[str]]:
    align_prompt = get_align_prompt(src_sub, tr_sub, src_part)
    
    parsed = ask_gpt(align_prompt, model=step5_align_model, response_json=True, log_title='align_subs')

    best = int(parsed['best_way'])
    align_data = parsed[f'align_way_{best}']
    
    src_parts = src_part.split('\n')
    tr_parts = [item[f'target_part_{i+1}'].strip() for i, item in enumerate(align_data)]
    
    print(f"🔗 Aligned parts:\nSRC_LANG:    {src_parts}\nTARGET_LANG: {tr_parts}\n")
    return src_parts, tr_parts

def split_align_subs(src_lines: List[str], tr_lines: List[str], max_retry=5) -> Tuple[List[str], List[str]]:
    from config import MAX_SRC_LENGTH, MAX_TARGET_LANGUAGE_LENGTH
    for attempt in range(max_retry):
        print(f"🔄 切割尝试第 {attempt + 1} 次")
        to_split = []
        
        for i, (en, tr) in enumerate(zip(src_lines, tr_lines)):
            if len(en) > MAX_SRC_LENGTH or calc_len(tr) > MAX_TARGET_LANGUAGE_LENGTH:
                to_split.append(i)
                print(f"📏 第 {i} 行需要切割:\nSRC_LANG:    {en}\nTARGET_LANG: {tr}\n")
        
        def process(i):
            split_en = split_sentence(src_lines[i], num_parts=2).strip()
            src_lines[i], tr_lines[i] = align_subs(src_lines[i], tr_lines[i], split_en)
        
        from config import MAX_WORKERS
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            executor.map(process, to_split)
        
        # Flatten `src_lines` and `tr_lines`
        src_lines = [item for sublist in src_lines for item in (sublist if isinstance(sublist, list) else [sublist])]
        tr_lines = [item for sublist in tr_lines for item in (sublist if isinstance(sublist, list) else [sublist])]
        
        if all(len(en) <= MAX_SRC_LENGTH for en in src_lines) and all(calc_len(tr) <= MAX_TARGET_LANGUAGE_LENGTH for tr in tr_lines):
            break
    
    return src_lines, tr_lines

def split_for_sub_main():
    if os.path.exists("output/log/translation_results_for_subtitles.xlsx"):
        print("🚨 文件 `translation_results_for_subtitles.xlsx` 已经存在，跳过此步。")
        return

    print('🚀 开始字幕分割...')
    df = pd.read_excel("output/log/translation_results.xlsx")
    src_lines = df['Source'].tolist()
    tr_lines = df['Translation'].tolist()
    src_lines, tr_lines = split_align_subs(src_lines, tr_lines, max_retry=5)
    pd.DataFrame({'Source': src_lines, 'Translation': tr_lines}).to_excel("output/log/translation_results_for_subtitles.xlsx", index=False)
    print('✅ 字幕分割完成！')

if __name__ == '__main__':
    split_for_sub_main()