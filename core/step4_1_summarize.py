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

def search_things_to_note_in_prompt(sentence):
    """Search for terms to note in the given sentence"""
    with open('output/log/terminology.json', 'r', encoding='utf-8') as file:
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
    src_content = combine_chunks()
    summary_prompt = get_summary_prompt(src_content)
    print("📝 Summarizing... Please wait a moment...")
    def valid_summary(response_data):
        # check if the terms is in the response_data
        if 'terms' not in response_data:
            return {"status": "error", "message": "Missing required key: terms"}
        return {"status": "success", "message": "Summary completed"}
    summary = ask_gpt(summary_prompt, response_json=True, valid_def=valid_summary, log_title='summary')

    with open('output/log/terminology.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=4)

    print('💾 Summary log saved to → `output/log/terminology.json`')

if __name__ == '__main__':
    get_summary()