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
    console.print("[yellow]开始新的镜像速度测试[/yellow]")
    
    # First test PyPI official mirror
    pypi_name = next(name for name, url in MIRRORS.items() if "pypi.org" in url)
    pypi_url = MIRRORS[pypi_name]
    console.print("[cyan]测试PyPI官方镜像...[/cyan]")
    
    optimal_thread_count = get_optimal_thread_count()
    console.print(f"使用 {optimal_thread_count} 个线程进行测试")
    
    _, pypi_speed = test_mirror_speed(pypi_name, pypi_url)
    
    if pypi_speed < FAST_THRESHOLD:
        console.print(f"PyPI官方镜像速度很快 ({pypi_speed:.2f} ms)。使用官方镜像。")
        set_pip_mirror(pypi_url, "pypi.org")
        return
    elif pypi_speed < SLOW_THRESHOLD:
        console.print(f"PyPI官方镜像速度可以接受 ({pypi_speed:.2f} ms)。您可以继续使用它。")
        return

    console.print(f"PyPI官方镜像速度较慢 ({pypi_speed:.2f} ms)。测试其他镜像...")

    # Test other mirrors
    speeds = {}
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    ) as progress:
        task = progress.add_task("[cyan]测试镜像...", total=len(MIRRORS) - 1)  # -1 because we already tested PyPI
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=optimal_thread_count) as executor:
            future_to_mirror = {executor.submit(test_mirror_speed, name, url): name for name, url in MIRRORS.items() if name != pypi_name}
            for future in concurrent.futures.as_completed(future_to_mirror):
                name = future_to_mirror[future]
                try:
                    name, speed = future.result()
                    if speed != float('inf'):
                        speeds[name] = speed
                except Exception as exc:
                    print(f'{name} 生成了一个异常: {exc}')
                finally:
                    progress.update(task, advance=1)

    table = Table(title="镜像速度测试结果")
    table.add_column("镜像", style="cyan")
    table.add_column("响应时间 (ms)", justify="right", style="magenta")

    for name, speed in sorted(speeds.items(), key=lambda x: x[1]):
        table.add_row(name, f"{speed:.2f}")

    console.print(table)

    if speeds:
        fastest_mirror = min(speeds, key=speeds.get)
        fastest_url = MIRRORS[fastest_mirror]
        console.print(f"\n[green]最快的镜像: {fastest_mirror} ({fastest_url})[/green]")
        console.print(f"[green]响应时间: {speeds[fastest_mirror]:.2f} ms[/green]")
        
        host = fastest_url.split("//")[1].split("/")[0]
        if set_pip_mirror(fastest_url, host):
            current_mirror = get_current_pip_mirror()
            console.print(f"\n[yellow]当前pip源: {current_mirror}[/yellow]")
            
            if current_mirror == fastest_url:
                console.print(f"[bold green]成功切换到 {fastest_mirror} 镜像。[/bold green]")
            else:
                console.print("[bold red]切换失败。当前pip源与预期不符。[/bold red]")
                console.print(f"[yellow]预期的pip源: {fastest_url}[/yellow]")
                console.print("[yellow]请手动检查配置或尝试以管理员权限运行此脚本。[/yellow]")
        else:
            console.print("[bold red]切换镜像失败，将继续使用当前源。[/bold red]")
            current_mirror = get_current_pip_mirror()
            console.print(f"[yellow]当前pip源: {current_mirror}[/yellow]")
            console.print("[yellow]请检查是否有足够的权限修改pip配置。[/yellow]")
    else:
        console.print("[bold red]所有镜像都无法访问。请检查您的网络连接。[/bold red]")

if __name__ == "__main__":
    main()
