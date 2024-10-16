import subprocess
import time
import requests
import os
import concurrent.futures
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

MIRRORS = {
    "Alibaba Cloud": "https://mirrors.aliyun.com/pypi/simple",
    "Tsinghua University": "https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple",
    "Huawei Cloud": "https://repo.huaweicloud.com/repository/pypi/simple",
    "Tencent Cloud": "https://mirrors.cloud.tencent.com/pypi/simple",
    "163 Cloud": "https://mirrors.163.com/pypi/simple",
    "PyPI Official": "https://pypi.org/simple"
}

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
    console.print("[yellow]Starting new mirror speed test[/yellow]")
    
    # First test PyPI official mirror
    pypi_name = next(name for name, url in MIRRORS.items() if "pypi.org" in url)
    pypi_url = MIRRORS[pypi_name]
    console.print("[cyan]Testing PyPI official mirror...[/cyan]")
    
    optimal_thread_count = get_optimal_thread_count()
    console.print(f"Using {optimal_thread_count} threads for testing")
    
    _, pypi_speed = test_mirror_speed(pypi_name, pypi_url)
    
    if pypi_speed < FAST_THRESHOLD:
        console.print(f"PyPI official mirror is fast ({pypi_speed:.2f} ms). Using the official mirror.")
        set_pip_mirror(pypi_url, "pypi.org")
        return
    elif pypi_speed < SLOW_THRESHOLD:
        console.print(f"PyPI official mirror speed is acceptable ({pypi_speed:.2f} ms). You may continue using it.")
        return

    console.print(f"PyPI official mirror is slow ({pypi_speed:.2f} ms). Testing other mirrors...")

    # Test other mirrors
    speeds = {}
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    ) as progress:
        task = progress.add_task("[cyan]Testing mirrors...", total=len(MIRRORS) - 1)  # -1 because we already tested PyPI
        
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

    table = Table(title="Mirror Speed Test Results")
    table.add_column("Mirror", style="cyan")
    table.add_column("Response Time (ms)", justify="right", style="magenta")

    for name, speed in sorted(speeds.items(), key=lambda x: x[1]):
        table.add_row(name, f"{speed:.2f}")

    console.print(table)

    if speeds:
        fastest_mirror = min(speeds, key=speeds.get)
        fastest_url = MIRRORS[fastest_mirror]
        console.print(f"\n[green]Fastest mirror: {fastest_mirror} ({fastest_url})[/green]")
        console.print(f"[green]Response time: {speeds[fastest_mirror]:.2f} ms[/green]")
        
        host = fastest_url.split("//")[1].split("/")[0]
        if set_pip_mirror(fastest_url, host):
            current_mirror = get_current_pip_mirror()
            console.print(f"\n[yellow]Current pip source: {current_mirror}[/yellow]")
            
            if current_mirror == fastest_url:
                console.print(f"[bold green]Successfully switched to {fastest_mirror} mirror.[/bold green]")
            else:
                console.print("[bold red]Switch failed. Current pip source doesn't match the expected one.[/bold red]")
                console.print(f"[yellow]Expected pip source: {fastest_url}[/yellow]")
                console.print("[yellow]Please check the configuration manually or try running this script with administrator privileges.[/yellow]")
        else:
            console.print("[bold red]Failed to switch mirror, will continue using the current source.[/bold red]")
            current_mirror = get_current_pip_mirror()
            console.print(f"[yellow]Current pip source: {current_mirror}[/yellow]")
            console.print("[yellow]Please check if you have sufficient permissions to modify pip configuration.[/yellow]")
    else:
        console.print("[bold red]All mirrors are unreachable. Please check your network connection.[/bold red]")

if __name__ == "__main__":
    main()
