import os
import gc
from batch.utils.settings_check import check_settings
from batch.utils.video_processor import process_video
from core.utils.config_utils import update_key
from core import workspace
import pandas as pd
from rich.console import Console
from rich.panel import Panel
import time

console = Console()

def ensure_workspace_columns(df):
    if 'Workspace' not in df.columns:
        df['Workspace'] = ''
    return df


def get_or_create_batch_workspace(row, index):
    current = row.get('Workspace', '')
    if isinstance(current, str) and current and os.path.exists(current):
        return current

    video_file = str(row['Video File'])
    source_is_url = video_file.startswith('http')
    job = workspace.create_job(
        name=os.path.splitext(os.path.basename(video_file))[0] or f"Batch Task {index + 1}",
        source_type='batch',
        source_path='' if source_is_url else video_file,
        source_url=video_file if source_is_url else '',
    )
    return job['path']


def record_and_update_config(source_language, target_language):
    if source_language and not pd.isna(source_language):
        update_key('whisper.language', source_language)
    if target_language and not pd.isna(target_language):
        update_key('target_language', target_language)

def process_batch():
    if not check_settings():
        raise Exception("Settings check failed")

    df = ensure_workspace_columns(pd.read_excel('batch/tasks_setting.xlsx'))
    for index, row in df.iterrows():
        if pd.isna(row['Status']) or 'Error' in str(row['Status']):
            total_tasks = len(df)
            video_file = row['Video File']
            workspace_path = get_or_create_batch_workspace(row, index)
            df.at[index, 'Workspace'] = workspace_path
            workspace.set_active_workspace(workspace_path)
            
            if not pd.isna(row['Status']) and 'Error' in str(row['Status']):
                console.print(Panel(f"Retrying failed task: {video_file}\nTask {index + 1}/{total_tasks}", 
                                 title="[bold yellow]Retry Task", expand=False))
            else:
                console.print(Panel(f"Now processing task: {video_file}\nTask {index + 1}/{total_tasks}", 
                                 title="[bold blue]Current Task", expand=False))
            
            source_language = row['Source Language']
            target_language = row['Target Language']
            
            record_and_update_config(source_language, target_language)
            
            try:
                dubbing = 0 if pd.isna(row['Dubbing']) else int(row['Dubbing'])
                is_retry = not pd.isna(row['Status']) and 'Error' in str(row['Status'])
                status, error_step, error_message = process_video(video_file, dubbing, is_retry)
                status_msg = "Done" if status else f"Error: {error_step} - {error_message}"
            except Exception as e:
                status_msg = f"Error: Unhandled exception - {str(e)}"
                console.print(f"[bold red]Error processing {video_file}: {status_msg}")
            finally:
                workspace.clear_active_workspace()
                
                df.at[index, 'Status'] = status_msg
                df.to_excel('batch/tasks_setting.xlsx', index=False)
                
                gc.collect()
                
                time.sleep(1)
        else:
            print(f"Skipping task: {row['Video File']} - Status: {row['Status']}")

    console.print(Panel("All tasks processed!\nCheck each row's `Workspace` folder for outputs.", 
                       title="[bold green]Batch Processing Complete", expand=False))

if __name__ == "__main__":
    process_batch()
