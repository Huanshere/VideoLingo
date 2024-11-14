import os, sys, json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.ask_gpt import ask_gpt
from core.prompts_storage import get_summary_prompt

TERMINOLOGY_JSON_PATH = 'output/log/terminology.json'
SENTENCE_TXT_PATH = 'output/log/sentence_splitbymeaning.txt'

def combine_chunks():
    """Combine the text chunks identified by whisper into a single long text"""
    with open(SENTENCE_TXT_PATH, 'r', encoding='utf-8') as file:
        sentences = file.readlines()
    cleaned_sentences = [line.strip() for line in sentences]
    combined_text = ' '.join(cleaned_sentences)
    return combined_text[:16000]  #! Return only the first 16000 characters

def search_things_to_note_in_prompt(sentence):
    """Search for terms to note in the given sentence"""
    with open(TERMINOLOGY_JSON_PATH, 'r', encoding='utf-8') as file:
        things_to_note = json.load(file)
    things_to_note_list = [term['src'] for term in things_to_note['terms'] if term['src'].lower() in sentence.lower()]
    if things_to_note_list:
        prompt = '\n'.join(
            f'{i+1}. "{term["src"]}": "{term["tgt"]}",'
            f' meaning: {term["note"]}'
            for i, term in enumerate(things_to_note['terms'])
            if term['src'] in things_to_note_list
        )
        return prompt
    else:
        return None

def get_summary():
    src_content = combine_chunks()
    summary_prompt = get_summary_prompt(src_content)
    print("📝 Summarizing and extracting terminology ...")
    
    def valid_summary(response_data):
        required_keys = {'src', 'tgt', 'note'}
        if 'terms' not in response_data:
            return {"status": "error", "message": "Invalid response format"}
        for term in response_data['terms']:
            if not all(key in term for key in required_keys):
                return {"status": "error", "message": "Invalid response format"}   
        return {"status": "success", "message": "Summary completed"}

    summary = ask_gpt(summary_prompt, response_json=True, valid_def=valid_summary, log_title='summary')
    
    with open(TERMINOLOGY_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=4)

    print(f'💾 Summary log saved to → `{TERMINOLOGY_JSON_PATH}`')

if __name__ == '__main__':
    get_summary()