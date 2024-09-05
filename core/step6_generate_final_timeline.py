import pandas as pd
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from difflib import SequenceMatcher
import re
from config import get_joiner, WHISPER_LANGUAGE
from core.step2_whisper_stamped import get_whisper_language

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
    return re.sub(r'[^\w\s]', '', text)

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
        start_index = word_index  # 记录当前句子开始的词索引

        while word_index < len(df_words):
            word = remove_punctuation(df_words['text'][word_index].lower())

            #! user joiner to join the sentence
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
            # 如果连续 3 个词都没有匹配，则跳出循环
            if decreasing_count >= 3:
                break
            word_index += 1
        
        if best_match['score'] <0.9:
            print("原句：", sentence)
            print("匹配：", best_match['phrase'])
            print("相似度：{:.2f}".format(best_match['score']))
            print("-" * 50)
            time_stamp_list.append((float(best_match['start']), float(best_match['end'])))
            word_index = start_index + best_match['word_count']  # 更新word_index到下一个句子的开始
        else:
            print(f"警告：无法为句子找到匹配: {sentence}")
        
        start_index = word_index  # 为下一个句子更新start_index
    
    return time_stamp_list

def align_timestamp(df_text, df_translate, for_audio = False):
    """Align timestamps and add a new timestamp column to df_translate"""
    df_trans_time = df_translate.copy()

    # Assign an ID to each word in df_text['text'] and create a new DataFrame
    words = df_text['text'].str.split(expand=True).stack().reset_index(level=1, drop=True).reset_index()
    words.columns = ['id', 'word']
    words['id'] = words['id'].astype(int)

    # Process timestamps ⏰
    time_stamp_list = get_sentence_timestamps(df_text, df_translate)
    df_trans_time['timestamp'] = time_stamp_list

    # 移除间隙 🕳️
    for i in range(len(df_trans_time)-1):
        delta_time = df_trans_time.loc[i+1, 'timestamp'][0] - df_trans_time.loc[i, 'timestamp'][1]
        if 0 < delta_time < 1:
            df_trans_time.at[i, 'timestamp'] = (df_trans_time.loc[i, 'timestamp'][0], df_trans_time.loc[i+1, 'timestamp'][0])

    # 将开始和结束时间戳转换为SRT格式
    df_trans_time['timestamp'] = df_trans_time['timestamp'].apply(lambda x: convert_to_srt_format(x[0], x[1]))

    # 美化字幕：替换Translation中的标点符号
    df_trans_time['Translation'] = df_trans_time['Translation'].apply(lambda x: re.sub(r'[,，。]', ' ', x).strip())

    # 输出字幕 📜
    def generate_subtitle_string(df, columns):
        return ''.join([f"{i+1}\n{row['timestamp']}\n{row[columns[0]].strip()}\n{row[columns[1]].strip() if len(columns) > 1 else ''}\n\n" for i, row in df.iterrows()]).strip()

    subtitle_configs = [
        ('src_subtitles.srt', ['Source']),
        ('trans_subtitles.srt', ['Translation']),
        ('bilingual_src_trans_subtitles.srt', ['Source', 'Translation']),
        ('bilingual_trans_src_subtitles.srt', ['Translation', 'Source'])
    ]

    output_dir = 'output/audio' if for_audio else 'output'
    os.makedirs(output_dir, exist_ok=True)

    for filename, columns in subtitle_configs:
        subtitle_str = generate_subtitle_string(df_trans_time, columns)
        with open(os.path.join(output_dir, filename), 'w', encoding='utf-8') as f:
            f.write(subtitle_str)

    if for_audio:
        # 为音频生成额外的字幕文件
        with open('output/audio/src_subs_for_audio.srt', 'w', encoding='utf-8') as f:
            f.write(generate_subtitle_string(df_trans_time, ['Source']))
        with open('output/audio/trans_subs_for_audio.srt', 'w', encoding='utf-8') as f:
            f.write(generate_subtitle_string(df_trans_time, ['Translation']))
    return df_trans_time

def align_timestamp_main():
    df_text = pd.read_excel('output/log/cleaned_chunks.xlsx')
    df_text['text'] = df_text['text'].str.strip('"').str.strip()
    df_translate = pd.read_excel('output/log/translation_results_for_subtitles.xlsx')
    df_translate['Translation'] = df_translate['Translation'].apply(lambda x: str(x).strip('。').strip('，').strip('"') if pd.notna(x) else '')
    # check if there's empty translation
    if (df_translate['Translation'].str.len() == 0).sum() > 0:
        raise ValueError(r'🚫 检测到空的翻译行！请手动检查 `output\log\translation_results_for_subtitles.xlsx` 中的空行填充内容，然后重新运行。')
    align_timestamp(df_text, df_translate)
    print('🎉📝 字幕生成成功！请在 `output` 文件夹中查看 👀')

    # for audio
    df_translate_for_audio = pd.read_excel('output/log/translation_results.xlsx')
    df_translate_for_audio['Translation'] = df_translate_for_audio['Translation'].apply(lambda x: str(x).strip('。').strip('，'))
    if (df_translate_for_audio['Translation'].str.len() == 0).sum() > 0:
        raise ValueError(r'🚫 检测到空的翻译行！请手动检查 `output\log\translation_results.xlsx` 中的空行填充内容，然后重新运行。')
    align_timestamp(df_text, df_translate_for_audio, for_audio=True)
    print('🎉📝 音频字幕生成成功！请在 `output/audio` 文件夹中查看 👀')
    

if __name__ == '__main__':
    align_timestamp_main()