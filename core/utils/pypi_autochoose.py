import time
import requests
import os
import concurrent.futures
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

MIRRORS = {
    "Tsinghua Mirror": "https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple",
    "PyPI Official": "https://pypi.org/simple"
}

console = Console()

FAST_THRESHOLD = 3000  # ms
SLOW_THRESHOLD = 5000  # ms

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

def main():
    """Return the fastest reachable index URL, or None. Never writes pip configuration."""
    console.print(Panel.fit("🚀 PyPI Mirror Speed Test", style="bold cyan"))
    
    # Test all mirrors simultaneously
    speeds = {}
    with Progress(
        SpinnerColumn(),
        TextColumn("[cyan]Testing mirrors...[/cyan]"),
    ) as progress:
        progress.add_task("", total=None)  # Indeterminate spinner
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=get_optimal_thread_count()) as executor:
            future_to_mirror = {executor.submit(test_mirror_speed, name, url): name 
                              for name, url in MIRRORS.items()}
            
            for future in concurrent.futures.as_completed(future_to_mirror):
                name = future_to_mirror[future]
                try:
                    name, speed = future.result()
                    if speed != float('inf'):
                        speeds[name] = speed
                except Exception as exc:
                    print(f'{name} generated an exception: {exc}')

    # Results display
    table = Table(show_header=False)
    table.add_column(style="cyan")
    table.add_column(justify="right", style="magenta")

    for name, speed in sorted(speeds.items(), key=lambda x: x[1]):
        table.add_row(name, f"{speed:.0f}ms")

    console.print(table)

    if not speeds:
        console.print("❌ All mirrors unreachable\n💡 Check network connection", style="red")
        return None
    fastest_mirror = min(speeds, key=speeds.get)
    console.print(f"✅ Fastest: {fastest_mirror}\n🔗 {MIRRORS[fastest_mirror]}", style="green")
    return MIRRORS[fastest_mirror]

if __name__ == "__main__":
    main()
