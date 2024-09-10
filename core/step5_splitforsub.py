import sys, os
import pandas as pd
from typing import List, Tuple
import concurrent.futures
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.step3_2_splitbymeaning import split_sentence
from core.ask_gpt import ask_gpt, step5_align_model
from core.prompts_storage import get_align_prompt

# ! You can modify your own weights here
# Chinese and Japanese 2.5 characters, Korean 2 characters, Thai 1.5 characters, full-width symbols 2 characters, other English-based and half-width symbols 1 character
def calc_len(text: str) -> float:
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
    
    parsed = ask_gpt(align_prompt, model=step5_align_model, response_json=True, valid_key='best_way', log_title='align_subs')

    best = int(parsed['best_way'])
    align_data = parsed[f'align_way_{best}']
    
    src_parts = src_part.split('\n')
    tr_parts = [item[f'target_part_{i+1}'].strip() for i, item in enumerate(align_data)]
    
    print(f"🔗 Aligned parts:\nSRC_LANG:    {src_parts}\nTARGET_LANG: {tr_parts}\n")
    return src_parts, tr_parts

def split_align_subs(src_lines: List[str], tr_lines: List[str], max_retry=5) -> Tuple[List[str], List[str]]:
    from config import MAX_SUB_LENGTH, TARGET_SUB_MULTIPLIER, MAX_WORKERS
    for attempt in range(max_retry):
        print(f"🔄 Split attempt {attempt + 1}")
        to_split = []
        
        for i, (src, tr) in enumerate(zip(src_lines, tr_lines)):
            src, tr = str(src), str(tr)
            if len(src) > MAX_SUB_LENGTH or calc_len(tr) * TARGET_SUB_MULTIPLIER > MAX_SUB_LENGTH:
                to_split.append(i)
                print(f"📏 Line {i} needs to be split:")
                print(f"Source Line:   {src}")
                print(f"Target Line:   {tr}")
                print()
        
        def process(i):
            split_src = split_sentence(src_lines[i], num_parts=2).strip()
            src_lines[i], tr_lines[i] = align_subs(src_lines[i], tr_lines[i], split_src)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            executor.map(process, to_split)
        
        # Flatten `src_lines` and `tr_lines`
        src_lines = [item for sublist in src_lines for item in (sublist if isinstance(sublist, list) else [sublist])]
        tr_lines = [item for sublist in tr_lines for item in (sublist if isinstance(sublist, list) else [sublist])]
        
        if all(len(src) <= MAX_SUB_LENGTH for src in src_lines) and all(calc_len(tr) * TARGET_SUB_MULTIPLIER <= MAX_SUB_LENGTH for tr in tr_lines):
            break
    
    return src_lines, tr_lines

def split_for_sub_main():
    if os.path.exists("output/log/translation_results_for_subtitles.xlsx"):
        print("🚨 File `translation_results_for_subtitles.xlsx` already exists, skipping this step.")
        return

    print('🚀 Start splitting subtitles...')
    df = pd.read_excel("output/log/translation_results.xlsx")
    src_lines = df['Source'].tolist()
    tr_lines = df['Translation'].tolist()
    src_lines, tr_lines = split_align_subs(src_lines, tr_lines, max_retry=5)
    pd.DataFrame({'Source': src_lines, 'Translation': tr_lines}).to_excel("output/log/translation_results_for_subtitles.xlsx", index=False)
    print('✅ Subtitles splitting completed!')

if __name__ == '__main__':
    split_for_sub_main()

    # # 短句
    # print(calc_len("你好")) # 4
    # print(calc_len("Hello")) # 5
    # print(calc_len("こんにちは")) # 5
    # print(calc_len("안녕하세요")) # 5
    # print(calc_len("สวัสดี")) # 3

    # # 中等长度句子
    # print(calc_len("你好，世界！")) # 8
    # print(calc_len("Hello, world!")) # 13
    # print(calc_len("こんにちは、世界！")) # 10
    # print(calc_len("안녕하세요, 세계!")) # 10
    # print(calc_len("สวัสดีครับ, โลก!")) # 10

    # # 较长句子
    # print(calc_len("欢迎来到美丽的中国，希望你玩得开心！")) # 22
    # print(calc_len("Welcome to beautiful China, hope you have a great time!")) # 55
    # print(calc_len("美しい中国へようこそ、楽しい時間を過ごせますように！")) # 26
    # print(calc_len("아름다운 중국에 오신 것을 환영합니다. 즐거운 시간 보내세요!")) # 31
    # print(calc_len("ยินดีต้อนรับสู่ประเทศจีนที่สวยงาม หวังว่าคุณจะสนุกนะครับ!")) # 35
