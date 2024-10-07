import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from batch.utils.settings_check import check_settings
from batch.utils.video_processor import process_video
from core.config_utils import load_key, update_key
import pandas as pd
from rich.console import Console
from rich.panel import Panel
import time

console = Console()

def record_and_update_config(source_language, target_language):
    original_source_lang = load_key('whisper.language')
    original_target_lang = load_key('target_language')
    
    if source_language and not pd.isna(source_language):
        update_key('whisper.language', source_language)
    if target_language and not pd.isna(target_language):
        update_key('target_language', target_language)
    
    return original_source_lang, original_target_lang

def process_batch():
    if not check_settings():
        raise Exception("Settings check failed")

    df = pd.read_excel('batch/tasks_setting.xlsx')
    for index, row in df.iterrows():
        if pd.isna(row['Status']):
            total_tasks = len(df)
            console.print(Panel(f"Now processing task: {row['Video File']}\nTask {index + 1}/{total_tasks}", title="[bold blue]Current Task", expand=False))
            source_language = row['Source Language']
            target_language = row['Target Language']
            
            # Record current config and update if necessary
            original_source_lang, original_target_lang = record_and_update_config(source_language, target_language)
            
            try:
                dubbing = 0 if pd.isna(row['Dubbing']) else int(row['Dubbing'])
                status, error_step, error_message = process_video(row['Video File'], dubbing)
                status_msg = "Done" if status else f"Error: {error_step} - {error_message}"
            finally:
                # Restore original config
                update_key('whisper.language', original_source_lang)
                update_key('target_language', original_target_lang)
            # update excel Status column
            df.at[index, 'Status'] = status_msg
            df.to_excel('batch/tasks_setting.xlsx', index=False)
            time.sleep(1)
        else:
            print(f"Skipping task: {row['Video File']} - Status: {row['Status']}")

    console.print(Panel("All tasks processed!\nCheck out in `batch/output`!", title="[bold green]Batch Processing Complete", expand=False))

if __name__ == "__main__":
    process_batch()