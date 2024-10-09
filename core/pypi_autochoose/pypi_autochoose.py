import subprocess
import time
import requests
import os
import locale
import concurrent.futures
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

FAST_THRESHOLD = 1000  # ms
SLOW_THRESHOLD = 1500  # ms

def get_optimal_thread_count():
    try:
        cpu_count = os.cpu_count()
        return max(cpu_count - 1, 1)
    except:
        return 2

def test_mirror_speed(name, url):
    try:
        start_time = time.time()
        response = requests.get(url, timeout=5)
        end_time = time.time()
        if response.status_code == 200:
            speed = (end_time - start_time) * 1000 
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

def main():
    console.print(Panel.fit(MESSAGES["checking_speeds"], style="bold magenta"))

    console.print(f"[yellow]{MESSAGES['starting_new_test']}[/yellow]")
    optimal_thread_count = get_optimal_thread_count()
    console.print(MESSAGES["using_threads"].format(optimal_thread_count))

    # 首先测试 PyPI 官方源
    pypi_name = next(name for name, url in MIRRORS.items() if "pypi.org" in url)
    pypi_url = MIRRORS[pypi_name]
    console.print(f"[cyan]{MESSAGES['testing_official_mirror']}[/cyan]")
    _, pypi_speed = test_mirror_speed(pypi_name, pypi_url)
    
    if pypi_speed < FAST_THRESHOLD:
        console.print(MESSAGES["official_mirror_fast"].format(pypi_speed))
        set_pip_mirror(pypi_url, "pypi.org")
        return
    elif pypi_speed < SLOW_THRESHOLD:
        console.print(MESSAGES["official_mirror_acceptable"].format(pypi_speed))
        return

    console.print(MESSAGES["official_mirror_slow"].format(pypi_speed))

    speeds = {}
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    ) as progress:
        task = progress.add_task(f"[cyan]{MESSAGES['testing_mirrors']}", total=len(MIRRORS))
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=optimal_thread_count) as executor:
            future_to_mirror = {executor.submit(test_mirror_speed, name, url): name for name, url in MIRRORS.items() if name != pypi_name}
            for future in concurrent.futures.as_completed(future_to_mirror):
                name = future_to_mirror[future]
                try:
                    name, speed = future.result()
                    if speed != float('inf'):
                        speeds[name] = speed
                except Exception as exc:
                    print(f'{name} generated an exception: {exc}')
                finally:
                    progress.update(task, advance=1)

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
