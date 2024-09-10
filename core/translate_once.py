import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.ask_gpt import ask_gpt
from core.prompts_storage import generate_shared_prompt, get_prompt_faithfulness, get_prompt_expressiveness

def translate_lines(lines, previous_content_prompt, after_cotent_prompt, things_to_note_prompt, summary_prompt, index = 0):
    from config import step4_2_translate_direct_model, step4_2_translate_free_model
    
    shared_prompt = generate_shared_prompt(previous_content_prompt, after_cotent_prompt, summary_prompt, things_to_note_prompt)

    ## Step 1: Faithful to the Original Text
    prompt1 = get_prompt_faithfulness(lines, shared_prompt)
    faith_result = ask_gpt(prompt1, model=step4_2_translate_direct_model, response_json=True, valid_key='1', log_title='translate_faithfulness')
    for i in faith_result:
        print(f'📄 Original Subtitle:   {faith_result[i]["Original Subtitle"]}')
        print(f'📚 Direct Translation:  {faith_result[i]["Direct Translation"]}')

    ## Step 2: Express Smoothly
    prompt2 = get_prompt_expressiveness(faith_result, lines, shared_prompt)
    express_result =  ask_gpt(prompt2, model=step4_2_translate_free_model, response_json=True, valid_key='1', log_title='translate_expressiveness') 
    for i in express_result:
        print(f'📄 Original Subtitle:   {express_result[i]["Original Subtitle"]}')
        print(f'🧠 Free Translation:    {express_result[i]["Free Translation"]}')
    translate_result = "\n".join([express_result[i]["Free Translation"].strip() for i in express_result])

    if len(lines.split('\n')) != len(translate_result.split('\n')):
        print(f'❌ Translation of block {index} failed')
    print(f'✅ Translation of block {index} completed')
    
    return translate_result, lines


if __name__ == '__main__':
    # test e.g.
    lines = '''All of you know Andrew Ng as a famous computer science professor at Stanford.
He was really early on in the development of neural networks with GPUs.
Of course, a creator of Coursera and popular courses like deeplearning.ai.
Also the founder and creator and early lead of Google Brain.'''
    previous_content_prompt = None
    after_cotent_prompt = None
    things_to_note_prompt = None
    summary_prompt = None
    translate_lines(lines, previous_content_prompt, after_cotent_prompt, things_to_note_prompt, summary_prompt)