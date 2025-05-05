import os
import gc
from batch.utils.settings_check import check_settings
from batch.utils.video_processor import process_video
from core.utils.config_utils import load_key, update_key
import pandas as pd
from rich.console import Console
from rich.panel import Panel
import time
import shutil

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
        if pd.isna(row['Status']) or 'Error' in str(row['Status']):
            total_tasks = len(df)
            video_file = row['Video File']
            
            if not pd.isna(row['Status']) and 'Error' in str(row['Status']):
                console.print(Panel(f"Retrying failed task: {video_file}\nTask {index + 1}/{total_tasks}", 
                                 title="[bold yellow]Retry Task", expand=False))
                
                # Restore files from batch/output/ERROR to output
                error_folder = os.path.join('batch', 'output', 'ERROR', os.path.splitext(video_file)[0])
                
                if os.path.exists(error_folder):
                    # Ensure the output folder exists
                    os.makedirs('output', exist_ok=True)
                    
                    # Copy all contents from ERROR folder for the specific video to output
                    for item in os.listdir(error_folder):
                        src_path = os.path.join(error_folder, item)
                        dst_path = os.path.join('output', item)
                        
                        if os.path.isdir(src_path):
                            if os.path.exists(dst_path):
                                shutil.rmtree(dst_path)
                            shutil.copytree(src_path, dst_path)
                        else:
                            if os.path.exists(dst_path):
                                os.remove(dst_path)
                            shutil.copy2(src_path, dst_path)
                            
                    console.print(f"[green]Restored files from ERROR folder for {video_file}")
                else:
                    console.print(f"[yellow]Warning: Error folder not found: {error_folder}")
            else:
                console.print(Panel(f"Now processing task: {video_file}\nTask {index + 1}/{total_tasks}", 
                                 title="[bold blue]Current Task", expand=False))
            
            source_language = row['Source Language']
            target_language = row['Target Language']
            
            original_source_lang, original_target_lang = record_and_update_config(source_language, target_language)
            
            try:
                dubbing = 0 if pd.isna(row['Dubbing']) else int(row['Dubbing'])
                is_retry = not pd.isna(row['Status']) and 'Error' in str(row['Status'])
                status, error_step, error_message = process_video(video_file, dubbing, is_retry)
                status_msg = "Done" if status else f"Error: {error_step} - {error_message}"
            except Exception as e:
                status_msg = f"Error: Unhandled exception - {str(e)}"
                console.print(f"[bold red]Error processing {video_file}: {status_msg}")
            finally:
                update_key('whisper.language', original_source_lang)
                update_key('target_language', original_target_lang)
                
                df.at[index, 'Status'] = status_msg
                df.to_excel('batch/tasks_setting.xlsx', index=False)
                
                gc.collect()
                
                time.sleep(1)
        else:
            print(f"Skipping task: {row['Video File']} - Status: {row['Status']}")

    console.print(Panel("All tasks processed!\nCheck out in `batch/output`!", 
                       title="[bold green]Batch Processing Complete", expand=False))

if __name__ == "__main__":
    process_batch()