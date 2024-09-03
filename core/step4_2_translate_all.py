import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.step4_2_translate_once import translate_lines
import pandas as pd
import concurrent.futures
from core.step4_1_summarize import search_things_to_note_in_prompt, get_theme_prompt

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
    from config import MAX_WORKERS
    # Check if the file exists
    if os.path.exists("output/log/translation_results.xlsx"):
        print("🚨 The file `translation_results.xlsx` already exists, skipping this step.")
        return
    
    chunks = split_chunks_by_chars()
    theme_prompt = get_theme_prompt()

    # 🔄 Use concurrent execution for translation
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for i, chunk in enumerate(chunks):
            future = executor.submit(translate_chunk, chunk, chunks, theme_prompt, i)
            futures.append(future)

        results = []
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda x: x[0])  # Sort results based on original order
    
    # 💾 Save results to lists and Excel file
    en_text, trans_text = [], []
    for _, chunk, translation in results:
        en_text.extend(chunk.split('\n'))
        trans_text.extend(translation.split('\n'))
    pd.DataFrame({'English': en_text, 'Translation': trans_text}).to_excel("output/log/translation_results.xlsx", index=False)


if __name__ == '__main__':
    translate_all()