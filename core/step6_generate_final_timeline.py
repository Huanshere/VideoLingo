import pandas as pd
import os
import string

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

def align_timestamp(df_text, df_translate, for_audio = False):
    """Align timestamps and add a new timestamp column to df_translate"""
    df_trans_time = df_translate.copy()

    #! 特殊符号特殊处理
    # 1. 把df_translate['Source']中每一句的"-"替换为" ",(避免连词)
    df_translate['Source'] = df_translate['Source'].str.replace('-', ' ')
    # 2. 所有,和.都替换为" "，然后把"  "替换为" "（避免大数字）
    df_translate['Source'] = df_translate['Source'].str.replace(',', ' ').str.replace('.', ' ').str.replace('  ', ' ')
    # 3. 使用string.punctuation删除所有标点符号
    df_text['text'] = df_text['text'].str.translate(str.maketrans('', '', string.punctuation))
    df_translate['Source'] = df_translate['Source'].str.translate(str.maketrans('', '', string.punctuation))
    # 4. 转换为小写
    df_text['text'] = df_text['text'].str.lower()
    df_translate['Source'] = df_translate['Source'].str.lower()

    # Assign an ID to each word in df_text['text'] and create a new DataFrame
    words = df_text['text'].str.split(expand=True).stack().reset_index(level=1, drop=True).reset_index()
    words.columns = ['id', 'word']
    words['id'] = words['id'].astype(int)

    # Process timestamps ⏰
    time_stamp_list = []
    word_index = 0
    line_index = 0
    

    for line in df_translate['Source']:
        line_words = line.split()
        line_word_index = 0
        start_time_id = None

        while line_word_index < len(line_words):
            if line_words[line_word_index] == words['word'][word_index]:
                if start_time_id is None:
                    start_time_id = words['id'][word_index]
                line_word_index += 1
                word_index += 1
            else:
                # Check if the next word in both dataframes match
                if (line_word_index + 1 < len(line_words) and word_index + 1 < len(words) and
                        line_words[line_word_index + 1] == words['word'][word_index + 1]):
                    # If so, consider it a minor error and replace the current word
                    print(f'Warning: Word mismatch @line{line_index}, replacing \'{line_words[line_word_index]}\' with \'{words["word"][word_index]}\'')
                    line_words[line_word_index] = words['word'][word_index]
                    start_time_id = words['id'][word_index]
                    line_word_index += 1
                    word_index += 1
                else:
                    input(f'Error: Word mismatch @line{line_index}\nExpected: \'{words["word"][word_index]}\', Actual: \'{line_words[line_word_index]}\', Word index: {word_index}')

        start_time = df_text['start'][start_time_id]
        end_time_id = words['id'][word_index - 1]
        end_time = df_text['end'][end_time_id]
        time_stamp_list.append((float(start_time), float(end_time)))

        line_index += 1

    df_trans_time['timestamp'] = time_stamp_list

    # Remove gaps 🕳️
    for i in range(len(df_trans_time)-1):
        delta_time = df_trans_time.loc[i+1, 'timestamp'][0] - df_trans_time.loc[i, 'timestamp'][1]
        if 0 < delta_time < 1:
            df_trans_time.at[i, 'timestamp'] = (df_trans_time.loc[i, 'timestamp'][0], df_trans_time.loc[i+1, 'timestamp'][0])

    # Convert start and end timestamps to SRT format
    df_trans_time['timestamp'] = df_trans_time['timestamp'].apply(lambda x: convert_to_srt_format(x[0], x[1]))

    # Output subtitles 📜
    src_sub_str = ''.join([f"{i}\n{row['timestamp']}\n{row['Source']}\n\n" for i, row in df_trans_time.iterrows()]).strip()
    trans_sub_str = ''.join([f"{i}\n{row['timestamp']}\n{row['Translation']}\n\n" for i, row in df_trans_time.iterrows()]).strip()
    src_trans_sub_str = ''.join([f"{i}\n{row['timestamp']}\n{row['Source']}\n{row['Translation']}\n\n" for i, row in df_trans_time.iterrows()]).strip()
    trans_en_sub_str = ''.join([f"{i}\n{row['timestamp']}\n{row['Translation']}\n{row['Source']}\n\n" for i, row in df_trans_time.iterrows()]).strip()

    if not for_audio:
        os.makedirs('output', exist_ok=True)
        with open('output/src_subtitles.srt', 'w', encoding='utf-8') as f:
            f.write(src_sub_str)
        with open('output/trans_subtitles.srt', 'w', encoding='utf-8') as f:
            f.write(trans_sub_str)
        with open('output/bilingual_src_trans_subtitles.srt', 'w', encoding='utf-8') as f:
            f.write(src_trans_sub_str)
        with open('output/bilingual_trans_src_subtitles.srt', 'w', encoding='utf-8') as f:
            f.write(trans_en_sub_str)
    else:
        os.makedirs('output/audio', exist_ok=True)
        with open('output/audio/src_subs_for_audio.srt', 'w', encoding='utf-8') as f:
            f.write(src_sub_str)
        with open('output/audio/trans_subs_for_audio.srt', 'w', encoding='utf-8') as f:
            f.write(trans_sub_str)
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