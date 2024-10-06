import subprocess
import time
import requests
import concurrent.futures
import os

# 定义要测试的镜像源列表
mirrors = {
    "PyPI官方": "https://pypi.org/simple",
    "阿里云": "https://mirrors.aliyun.com/pypi/simple",
    "清华大学": "https://pypi.tuna.tsinghua.edu.cn/simple",
    "中国科技大学": "https://pypi.mirrors.ustc.edu.cn/simple",
    "豆瓣": "https://pypi.doubanio.com/simple",
    "华为云": "https://repo.huaweicloud.com/repository/pypi/simple",
    "腾讯云": "https://mirrors.cloud.tencent.com/pypi/simple",
    "Google": "https://pypi.org/simple",
    "Cloudflare": "https://pypi.cloudflare.com/simple",
    "Azure中国": "https://mirrors.azure.cn/pypi/simple",
    "ReadTheDocs": "https://pypi.readthedocs.org/simple",
    "CERN": "https://pypi.cern.ch/simple"
}


def get_optimal_thread_count():
    try:
        # 获取CPU的线程数
        cpu_count = os.cpu_count()
        # 使用线程数的一半，但不少于1个线程
        return max(cpu_count // 2, 1)
    except:
        # 如果无法获取CPU信息，默认使用2个线程
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

def main():
    print("正在测试镜像源速度...")
    
    # 获取最优线程数
    optimal_thread_count = get_optimal_thread_count()
    print(f"使用 {optimal_thread_count} 个线程进行测试")

    # 使用最优线程数进行测试
    with concurrent.futures.ThreadPoolExecutor(max_workers=optimal_thread_count) as executor:
        future_to_url = {executor.submit(test_mirror_speed, name, url): name for name, url in mirrors.items()}
        speeds = {}
        for future in concurrent.futures.as_completed(future_to_url):
            name, speed = future.result()
            if speed != float('inf'):
                speeds[name] = speed
                print(f"{name}: {speed:.2f} ms")
            else:
                print(f"{name}: 连接失败")

    if speeds:
        fastest_mirror = min(speeds, key=speeds.get)
        fastest_url = mirrors[fastest_mirror]
        print(f"\n最快的镜像源是: {fastest_mirror} ({fastest_url})")
        print(f"响应时间: {speeds[fastest_mirror]:.2f} ms")
        
        host = fastest_url.split("//")[1].split("/")[0]
        if set_pip_mirror(fastest_url, host):
            current_mirror = get_current_pip_mirror()
            print(f"当前的pip源是: {current_mirror}")
            
            if current_mirror == fastest_url:
                print(f"已成功切换到 {fastest_mirror} 镜像源。")
            else:
                print(f"切换失败。当前pip源与预期不符。")
                print(f"预期的pip源: {fastest_url}")
                print("请手动检查配置或尝试以管理员权限运行此脚本。")
        else:
            print("切换镜像源失败，将继续使用当前源。")
            current_mirror = get_current_pip_mirror()
            print(f"当前的pip源是: {current_mirror}")
            print("请检查是否有足够的权限来修改pip配置。")
    else:
        print("所有镜像源都无法连接，请检查网络连接。")

if __name__ == "__main__":
    main()
