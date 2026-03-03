import subprocess
import sys
import os
import signal
import atexit

# 全局变量，用于跟踪服务器进程
capcut_server_process = None

# 启动剪映服务器的函数
def start_capcut_server():
    global capcut_server_process
    
    # 如果服务器已经在运行，则不需要再次启动
    if capcut_server_process and capcut_server_process.poll() is None:
        return
    
    try:
        # 获取capcut_server.py的绝对路径
        server_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                  "capcut_api", "capcut_server.py")
        
        # 启动服务器进程
        process = subprocess.Popen([sys.executable, server_path],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        
        # 保存进程引用
        capcut_server_process = process
        
    except Exception as e:
        print(f"Error starting capcut server: {e}")

# 停止剪映服务器的函数
def stop_capcut_server():
    global capcut_server_process
    
    # 如果进程存在且仍在运行，则终止进程
    if capcut_server_process and capcut_server_process.poll() is None:
        try:
            capcut_server_process.terminate()
            try:
                capcut_server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                capcut_server_process.kill()
        except Exception as e:
            print(f"Error stopping capcut server: {e}")

# 注册退出处理函数，确保在应用退出时停止服务器
def cleanup_capcut_server():
    stop_capcut_server()

atexit.register(cleanup_capcut_server)

# 处理信号，确保在接收到终止信号时停止服务器
def signal_handler(sig, frame):
    cleanup_capcut_server()
    sys.exit(0)

# 注册信号处理器
try:
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
except ValueError:
    # 如果在非主线程中执行，忽略错误
    pass