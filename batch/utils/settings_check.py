import os
import pandas as pd
from rich.console import Console
from rich.panel import Panel

# Constants
SETTINGS_FILE = 'batch/tasks_setting.xlsx'
INPUT_FOLDER = os.path.join('batch', 'input')
VALID_DUBBING_VALUES = [0, 1]

console = Console()

def check_settings():
    os.makedirs(INPUT_FOLDER, exist_ok=True)
    df = pd.read_excel(SETTINGS_FILE)
    input_files = set(os.listdir(INPUT_FOLDER))
    excel_files = set(df['Video File'].tolist())
    files_not_in_excel = input_files - excel_files

    all_passed = True
    local_video_tasks = 0
    url_tasks = 0

    if files_not_in_excel:
        console.print(Panel(
            "\n".join([f"- {file}" for file in files_not_in_excel]),
            title="[bold red]Warning: Files in input folder not mentioned in Excel sheet",
            expand=False
        ))
        all_passed = False

    for index, row in df.iterrows():
        video_file = row['Video File']
        source_language = row['Source Language']
        dubbing = row['Dubbing']

        if video_file.startswith('http'):
            url_tasks += 1
        elif os.path.isfile(os.path.join(INPUT_FOLDER, video_file)):
            local_video_tasks += 1
        else:
            console.print(Panel(f"Invalid video file or URL 「{video_file}」", title=f"[bold red]Error in row {index + 2}", expand=False))
            all_passed = False

        if not pd.isna(dubbing):
            if int(dubbing) not in VALID_DUBBING_VALUES:
                console.print(Panel(f"Invalid dubbing value 「{dubbing}」", title=f"[bold red]Error in row {index + 2}", expand=False))
                all_passed = False

    if all_passed:
        console.print(Panel(f"✅ All settings passed the check!\nDetected {local_video_tasks} local video tasks and {url_tasks} URL tasks.", title="[bold green]Success", expand=False))

    return all_passed


if __name__ == "__main__":  
    check_settings()