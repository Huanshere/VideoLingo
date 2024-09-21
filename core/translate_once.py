import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.ask_gpt import ask_gpt
from core.prompts_storage import generate_shared_prompt, get_prompt_faithfulness, get_prompt_expressiveness
from rich.panel import Panel
from rich.console import Console
from rich.table import Table
import re

console = Console()

def valid_translate_result(result: dict, required_keys: list, required_sub_keys: list):
    if not isinstance(result, dict):
        return {"status": "error", "message": "Result is not a dictionary"}
    
    # Check for the required key
    if not all(key in result for key in required_keys):
        return {"status": "error", "message": f"Missing required key(s): {', '.join(set(required_keys) - set(result.keys()))}"}
    
    # Check for required sub-keys in all items
    for key in result:
        if not all(sub_key in result[key] for sub_key in required_sub_keys):
            return {"status": "error", "message": f"Missing required sub-key(s) in item {key}: {', '.join(set(required_sub_keys) - set(result[key].keys()))}"}
    
    # Check if all sub-keys values are not empty
    def remove_punctuation(text):
        return re.sub(r'[^\w\s]', '', text)
    for key in result:
        for sub_key in required_sub_keys:
            translate_result = remove_punctuation(result[key][sub_key]).strip()
            if not translate_result:
                return {"status": "error", "message": f"Empty value for sub-key '{sub_key}' in item {key}"}
    
    return {"status": "success", "message": "Translation completed"}

def translate_lines(lines, previous_content_prompt, after_cotent_prompt, things_to_note_prompt, summary_prompt, index = 0):
    shared_prompt = generate_shared_prompt(previous_content_prompt, after_cotent_prompt, summary_prompt, things_to_note_prompt)

    # Retry translation if the length of the original text and the translated text are not the same, or if the specified key is missing
    def retry_translation(prompt, step_name):
        def valid_faith(response_data):
            return valid_translate_result(response_data, ['1'], ['Direct Translation'])
        def valid_express(response_data):
            return valid_translate_result(response_data, ['1'], ['Free Translation'])
        for retry in range(3):
            if step_name == 'faithfulness':
                result = ask_gpt(prompt, response_json=True, valid_def=valid_faith, log_title=f'translate_{step_name}')
            elif step_name == 'expressiveness':
                result = ask_gpt(prompt, response_json=True, valid_def=valid_express, log_title=f'translate_{step_name}')
            if len(lines.split('\n')) == len(result):
                return result
            if retry != 2:
                console.print(f'[yellow]⚠️ {step_name.capitalize()} translation of block {index} failed, Retry...[/yellow]')
        raise ValueError(f'[red]❌ {step_name.capitalize()} translation of block {index} failed after 3 retries. Please check your input text.[/red]')

    ## Step 1: Faithful to the Original Text
    prompt1 = get_prompt_faithfulness(lines, shared_prompt)
    faith_result = retry_translation(prompt1, 'faithfulness')

    for i in faith_result:
        faith_result[i]["Direct Translation"] = faith_result[i]["Direct Translation"].replace('\n', ' ')

    ## Step 2: Express Smoothly  
    prompt2 = get_prompt_expressiveness(faith_result, lines, shared_prompt)
    express_result = retry_translation(prompt2, 'expressiveness')

    table = Table(title="Translation Results")
    table.add_column("Translations", style="cyan")

    for i, key in enumerate(express_result):
        table.add_row(f"[cyan]Original: {faith_result[key]['Original Subtitle']}[/cyan]")
        table.add_row(f"[magenta]Direct:   {faith_result[key]['Direct Translation']}[/magenta]")
        table.add_row(f"[green]Free:     {express_result[key]['Free Translation']}[/green]")
        if i < len(express_result) - 1:
            table.add_row("[yellow]" + "-" * 50 + "[/yellow]")

    console.print(table)

    translate_result = "\n".join([express_result[i]["Free Translation"].replace('\n', ' ').strip() for i in express_result])

    if len(lines.split('\n')) != len(translate_result.split('\n')):
        console.print(Panel(f'[red]❌ Translation of block {index} failed, Length Mismatch, Please check `output/gpt_log/translate_expressiveness.json`[/red]'))
        raise ValueError(f'Original ···{lines}···,\nbut got ···{translate_result}···')
    else:
        console.print(Panel(f'[green]✅ Translation of block {index} completed[/green]'))

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