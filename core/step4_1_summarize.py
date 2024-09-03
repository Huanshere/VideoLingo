import os, sys, json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.ask_gpt import ask_gpt
import pandas as pd
from core.prompts_storage import get_summary_prompt

def combine_chunks():
    """Combine the text chunks identified by whisper into a single long text"""
    df = pd.read_excel('output/log/cleaned_chunks.xlsx')
    df['text'] = df['text'].str.strip('"').str.strip()
    combined_text = ' '.join(df['text'])
    return combined_text

def search_things_to_note_in_prompt(sentence, things_to_note):
    """Search for terms to note in the given sentence, return prompt if found"""
    things_to_note_list = [term['original'] for term in things_to_note['terms'] if term['original'].lower() in sentence.lower()]
    if things_to_note_list:
        prompt = '\n'.join(
            f'{i+1}. "{term["original"]}":"{term["translation"]}",'
            f'{term["explanation"]}'
            for i, term in enumerate(things_to_note['terms'])
            if term['original'] in things_to_note_list
        )
        return prompt
    else:
        return None

def get_theme_prompt():
    with open('output/log/translate terminology.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    topic = data.get('theme', None)
    return topic

def search_things_to_note_in_prompt(sentence):
    """Search for terms to note in the given sentence"""
    with open('output/log/translate terminology.json', 'r', encoding='utf-8') as file:
        things_to_note = json.load(file)
    things_to_note_list = [term['original'] for term in things_to_note['terms'] if term['original'].lower() in sentence.lower()]
    if things_to_note_list:
        prompt = '\n'.join(
            f'{i+1}. "{term["original"]}": "{term["translation"]}",'
            f' meaning: {term["explanation"]}'
            for i, term in enumerate(things_to_note['terms'])
            if term['original'] in things_to_note_list
        )
        return prompt
    else:
        return None

def get_summary():
    from config import step4_1_summarize_model, TARGET_LANGUAGE
    English_content = combine_chunks()
    summary_prompt = get_summary_prompt(English_content, TARGET_LANGUAGE)
    summary = ask_gpt(summary_prompt, model=step4_1_summarize_model, response_json=True, log_title='summary')

    with open('output/log/translate terminology.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=4)

    print('💾 Summary log saved to → `output/log/translate terminology.json`')

if __name__ == '__main__':
    # get_summary()
    print(get_theme_prompt())