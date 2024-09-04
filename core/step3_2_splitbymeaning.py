import sys,os,math
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import concurrent.futures
from core.ask_gpt import ask_gpt
from core.prompts_storage import get_split_prompt
from difflib import SequenceMatcher

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
    from config import step3_2_split_model
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
    print_split = best_split.replace('\n',' [br] ')
    print(f"📚 Split Sentence: {print_split}")
    
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

def split_sentences_by_meaning():
    """按意义分割句子的主要函数。"""
    # 读取输入的句子
    with open('output/log/sentence_splitbynlp.txt', 'r', encoding='utf-8') as f:
        sentences = [line.strip() for line in f.readlines()]

    # 🔄 多次处理句子以确保全部被分割
    from config import MAX_WORKERS, MAX_SPLIT_LENGTH
    for retry_attempt in range(5):
        sentences = parallel_split_sentences(sentences, max_length=MAX_SPLIT_LENGTH, max_workers=MAX_WORKERS, retry_attempt=retry_attempt)

    # 💾 保存结果
    with open('output/log/sentence_splitbymeaning.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(sentences))
    print('✅ 所有句子已成功分割')

if __name__ == '__main__':
    # print(split_sentence('Which makes no sense to the... average guy who always pushes the character creation slider all the way to the right.', 2, 22))
    split_sentences_by_meaning()