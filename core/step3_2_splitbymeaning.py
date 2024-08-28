import sys,os,math
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import concurrent.futures
from core.ask_gpt import ask_gpt, step3_2_split_model
from core.prompts_storage import get_split_prompt
from difflib import SequenceMatcher
from config import MAX_SPLIT_LENGTH
import os
import requests
import logging

logger = logging.getLogger(__name__)

def find_split_positions(original, modified):
    split_positions = []
    parts = modified.split('[br]')
    start = 0

    for i in range(len(parts) - 1):  # Only iterate until the second-to-last part
        max_similarity = 0
        best_split = None

        for j in range(start, len(original)):
            if original[j] == ' ':
                original_left = original[start:j]
                modified_left = parts[i].strip()

                left_similarity = SequenceMatcher(None, original_left, modified_left).ratio()

                total_similarity = left_similarity

                if total_similarity > max_similarity:
                    max_similarity = total_similarity
                    best_split = j
        if max_similarity < 0.9:
            print(f"Warning: The best split found has low similarity {max_similarity}")
        if best_split is not None:
            split_positions.append(best_split)
            start = best_split + 1
        else:
            print(f"Warning: Could not find a good split for part {i+1}.")

    return split_positions

def split_sentence(sentence, num_parts, word_limit=18, index=-1, retry_attempt=0):
    """Split a long sentence using GPT and return the result as a string."""
    split_prompt = get_split_prompt(sentence, num_parts, word_limit)
    response_data = ask_gpt(split_prompt + ' ' * retry_attempt, model=step3_2_split_model, response_json=True, log_title='sentence_splitbymeaning')
    best_split_way = response_data[f"split_way_{response_data['best_way']}"]
    split_points = find_split_positions(sentence, best_split_way)
    # split the sentence based on the split points
    for i, split_point in enumerate(split_points):
        if i == 0:
            best_split = sentence[:split_point] + '\n' + sentence[split_point:]
        else:
            parts = best_split.split('\n')
            last_part = parts[-1]
            parts[-1] = last_part[:split_point - split_points[i-1]] + '\n' + last_part[split_point - split_points[i-1]:]
            best_split = '\n'.join(parts)
    if index != -1:
        print(f'✅ Sentence {index} has been successfully split')
    print(f'📄 Original English:   {sentence}')
    print(f"📚 Split Sentence: {best_split.replace('\n',' [br] ')}")
    
    return best_split

def parallel_split_sentences(sentences, max_length, max_workers, retry_attempt=0):
    """Split sentences in parallel using a thread pool."""
    new_sentences = [None] * len(sentences)
    futures = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for index, sentence in enumerate(sentences):
            tokens = sentence.split()
            num_parts = math.ceil(len(tokens) / max_length)
            if len(tokens) > max_length:
                future = executor.submit(split_sentence, sentence, num_parts, max_length, index=index, retry_attempt=retry_attempt)
                futures.append((future, index, num_parts, sentence))
            else:
                new_sentences[index] = [sentence]

        for future, index, num_parts, sentence in futures:
            split_result = future.result()
            if split_result:
                split_lines = split_result.strip().split('\n')
                new_sentences[index] = [line.strip() for line in split_lines]
            else:
                new_sentences[index] = [sentence]

    return [sentence for sublist in new_sentences for sentence in sublist]

def print_proxy_settings():
    logger.debug("当前代理设置:")
    for var in ['http_proxy', 'https_proxy', 'ftp_proxy', 'no_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'FTP_PROXY', 'NO_PROXY']:
        if var in os.environ:
            logger.debug(f"{var}: {os.environ[var]}")
    logger.debug("requests 库的当前代理设置:")
    logger.debug(requests.utils.getproxies())

def split_sentences_by_meaning():
    logger.info("开始执行 split_sentences_by_meaning 函数")
    print_proxy_settings()
    
    logger.debug("禁用 requests 库的代理")
    old_getproxies = requests.utils.getproxies
    requests.utils.getproxies = lambda: {}
    
    old_session = requests.Session
    requests.Session = lambda: type('MockSession', (), {'proxies': {}})()
    
    try:
        logger.debug("开始执行主要逻辑")
        # 在这里添加函数的主要逻辑，每个重要步骤都添加日志
        # 例如：
        # logger.debug("正在读取输入文件")
        # with open('input_file.txt', 'r') as f:
        #     content = f.read()
        # logger.debug(f"读取到的内容长度: {len(content)}")
        
        # logger.debug("开始处理内容")
        # processed_content = process_content(content)
        # logger.debug(f"处理后的内容长度: {len(processed_content)}")
        
        # logger.debug("开始写入输出文件")
        # with open('output_file.txt', 'w') as f:
        #     f.write(processed_content)
        # logger.debug("输出文件写入完成")
        
    except Exception as e:
        logger.exception("在 split_sentences_by_meaning 函数中发生异常")
        raise
    finally:
        logger.debug("恢复 requests 库的原始设置")
        requests.utils.getproxies = old_getproxies
        requests.Session = old_session

    logger.info("split_sentences_by_meaning 函数执行完成")
    # 返回结果
    # ...
    
    try:
        # Read input sentences
        with open('output/log/sentence_splitbymark.txt', 'r', encoding='utf-8') as f:
            sentences = [line.strip() for line in f.readlines()]

        max_length = MAX_SPLIT_LENGTH # 18以下会切太碎影响翻译，22 以上太长会导致后续为字幕切分难以对齐

        # 🔄 Process sentences multiple times to ensure all are split
        for retry_attempt in range(5):
            sentences = parallel_split_sentences(sentences, max_length=max_length, max_workers=8, retry_attempt=retry_attempt)

        # 💾 Save the results
        with open('output/log/sentence_splitbymeaning.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(sentences))
        print('✅ All sentences have been successfully split')

    finally:
        # 恢复 requests 库的原始代理设置
        requests.utils.getproxies = old_getproxies
        requests.Session = old_session

if __name__ == '__main__':
    print(split_sentence('Which makes no sense to the... average guy who always pushes the character creation slider all the way to the right.', 2, 22))
    # split_sentences_by_meaning()
