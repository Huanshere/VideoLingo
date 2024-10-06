import subprocess
import time
import requests
import concurrent.futures
import os
import json
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.panel import Panel

console = Console()

# 定义要测试的镜像源列表
mirrors = {
    "PyPI官方": "https://pypi.org/simple",
    "阿里云": "https://mirrors.aliyun.com/pypi/simple",
    "清华大学": "https://pypi.tuna.tsinghua.edu.cn/simple",
    "中国科技大学": "https://pypi.mirrors.ustc.edu.cn/simple",
    "华为云": "https://repo.huaweicloud.com/repository/pypi/simple",
    "腾讯云": "https://mirrors.cloud.tencent.com/pypi/simple",
    "Google": "https://pypi.org/simple",
    "Cloudflare": "https://pypi.cloudflare.com/simple",
    "Azure中国": "https://mirrors.azure.cn/pypi/simple",
    "ReadTheDocs": "https://pypi.readthedocs.org/simple",
    "CERN": "https://pypi.cern.ch/simple"
}

RESULTS_FILE = "mirror_test_results.json"
RESULTS_VALID_DURATION = timedelta(hours=1)  # 结果有效期为1小时

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
    console.print(Panel.fit("检查镜像源速度...", style="bold magenta"))

    speeds = load_previous_results()
    if speeds:
        console.print("[green]使用缓存的测试结果[/green]")
    else:
        console.print("[yellow]开始新的镜像源速度测试[/yellow]")
        optimal_thread_count = get_optimal_thread_count()
        console.print(f"使用 [cyan]{optimal_thread_count}[/cyan] 个线程进行测试")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            task = progress.add_task("[cyan]测试镜像源...", total=len(mirrors))
            with concurrent.futures.ThreadPoolExecutor(max_workers=optimal_thread_count) as executor:
                future_to_url = {executor.submit(test_mirror_speed, name, url): name for name, url in mirrors.items()}
                speeds = {}
                for future in concurrent.futures.as_completed(future_to_url):
                    name, speed = future.result()
                    if speed != float('inf'):
                        speeds[name] = speed
                    progress.update(task, advance=1)

        save_results(speeds)

    table = Table(title="镜像源速度测试结果")
    table.add_column("镜像源", style="cyan")
    table.add_column("响应时间 (ms)", justify="right", style="magenta")

    for name, speed in sorted(speeds.items(), key=lambda x: x[1]):
        table.add_row(name, f"{speed:.2f}")

    console.print(table)

    if speeds:
        fastest_mirror = min(speeds, key=speeds.get)
        fastest_url = mirrors[fastest_mirror]
        console.print(f"\n[green]最快的镜像源是:[/green] [bold cyan]{fastest_mirror}[/bold cyan] ({fastest_url})")
        console.print(f"[green]响应时间:[/green] [bold cyan]{speeds[fastest_mirror]:.2f} ms[/bold cyan]")
        
        host = fastest_url.split("//")[1].split("/")[0]
        if set_pip_mirror(fastest_url, host):
            current_mirror = get_current_pip_mirror()
            console.print(f"\n[yellow]当前的pip源是:[/yellow] [bold]{current_mirror}[/bold]")
            
            if current_mirror == fastest_url:
                console.print(f"[bold green]已成功切换到 {fastest_mirror} 镜像源。[/bold green]")
            else:
                console.print("[bold red]切换失败。当前pip源与预期不符。[/bold red]")
                console.print(f"[yellow]预期的pip源:[/yellow] [bold]{fastest_url}[/bold]")
                console.print("[yellow]请手动检查配置或尝试以管理员权限运行此脚本。[/yellow]")
        else:
            console.print("[bold red]切换镜像源失败，将继续使用当前源。[/bold red]")
            current_mirror = get_current_pip_mirror()
            console.print(f"[yellow]当前的pip源是:[/yellow] [bold]{current_mirror}[/bold]")
            console.print("[yellow]请检查是否有足够的权限来修改pip配置。[/yellow]")
    else:
        console.print("[bold red]所有镜像源都无法连接，请检查网络连接。[/bold red]")

if __name__ == "__main__":
    main()
