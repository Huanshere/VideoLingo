
import subprocess
import time
import requests
import concurrent.futures
import os
import json
import locale
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.panel import Panel

# 根据系统语言选择语言文件
system_language = locale.getdefaultlocale()[0]
if system_language.startswith('zh'):
    from .lang_zh import MESSAGES, MIRRORS
else:
    from .lang_en import MESSAGES, MIRRORS

console = Console()

RESULTS_FILE = "mirror_test_results.json"
RESULTS_VALID_DURATION = timedelta(hours=1)

def get_optimal_thread_count():
    try:
        cpu_count = os.cpu_count()
        return max(cpu_count // 2, 1)
    except:
        return 2

def test_mirror_speed(name, url):
    try:
        start_time = time.time()
        response = requests.get(url, timeout=5)
        end_time = time.time()
        if response.status_code == 200:
            speed = (end_time - start_time) * 1000  # 转换为毫秒
            return name, speed
        else:
            return name, float('inf')
    except requests.RequestException:
        return name, float('inf')

def set_pip_mirror(url, host):
    try:
        subprocess.run(["pip", "config", "set", "global.index-url", url], check=True, capture_output=True)
        subprocess.run(["pip", "config", "set", "install.trusted-host", host], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False

def get_current_pip_mirror():
    try:
        result = subprocess.run(["pip", "config", "get", "global.index-url"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def load_previous_results():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r') as f:
            data = json.load(f)
        test_time = datetime.fromisoformat(data['test_time'])
        if datetime.now() - test_time <= RESULTS_VALID_DURATION:
            return data['speeds']
    return None

def save_results(speeds):
    data = {
        'test_time': datetime.now().isoformat(),
        'speeds': speeds
    }
    with open(RESULTS_FILE, 'w') as f:
        json.dump(data, f)

def main():
    console.print(Panel.fit(MESSAGES["checking_speeds"], style="bold magenta"))

    speeds = load_previous_results()
    if speeds:
        console.print(f"[green]{MESSAGES['using_cached']}[/green]")
    else:
        console.print(f"[yellow]{MESSAGES['starting_new_test']}[/yellow]")
        optimal_thread_count = get_optimal_thread_count()
        console.print(MESSAGES["using_threads"].format(optimal_thread_count))

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            task = progress.add_task(f"[cyan]{MESSAGES['testing_mirrors']}", total=len(MIRRORS))
            with concurrent.futures.ThreadPoolExecutor(max_workers=optimal_thread_count) as executor:
                future_to_url = {executor.submit(test_mirror_speed, name, url): name for name, url in MIRRORS.items()}
                speeds = {}
                for future in concurrent.futures.as_completed(future_to_url):
                    name, speed = future.result()
                    if speed != float('inf'):
                        speeds[name] = speed
                    progress.update(task, advance=1)

        save_results(speeds)

    table = Table(title=MESSAGES["results_title"])
    table.add_column(MESSAGES["mirror_column"], style="cyan")
    table.add_column(MESSAGES["response_time_column"], justify="right", style="magenta")

    for name, speed in sorted(speeds.items(), key=lambda x: x[1]):
        table.add_row(name, f"{speed:.2f}")

    console.print(table)

    if speeds:
        fastest_mirror = min(speeds, key=speeds.get)
        fastest_url = MIRRORS[fastest_mirror]
        console.print(f"\n[green]{MESSAGES['fastest_mirror'].format(fastest_mirror, fastest_url)}[/green]")
        console.print(f"[green]{MESSAGES['response_time'].format(speeds[fastest_mirror])}[/green]")
        
        host = fastest_url.split("//")[1].split("/")[0]
        if set_pip_mirror(fastest_url, host):
            current_mirror = get_current_pip_mirror()
            console.print(f"\n[yellow]{MESSAGES['current_pip_source'].format(current_mirror)}[/yellow]")
            
            if current_mirror == fastest_url:
                console.print(f"[bold green]{MESSAGES['switch_success'].format(fastest_mirror)}[/bold green]")
            else:
                console.print(f"[bold red]{MESSAGES['switch_fail']}[/bold red]")
                console.print(f"[yellow]{MESSAGES['expected_source'].format(fastest_url)}[/yellow]")
                console.print(f"[yellow]{MESSAGES['manual_check']}[/yellow]")
        else:
            console.print(f"[bold red]{MESSAGES['switch_fail_permissions']}[/bold red]")
            current_mirror = get_current_pip_mirror()
            console.print(f"[yellow]{MESSAGES['current_pip_source'].format(current_mirror)}[/yellow]")
            console.print(f"[yellow]{MESSAGES['check_permissions']}[/yellow]")
    else:
        console.print(f"[bold red]{MESSAGES['all_unreachable']}[/bold red]")

if __name__ == "__main__":
    main()
