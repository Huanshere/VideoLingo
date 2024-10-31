@echo off
cd /d %~dp0
if exist runtime (
    echo 使用 runtime 文件夹...
    runtime\python.exe -m streamlit run st.py
) else (
    echo 未找到 runtime 文件夹，使用 conda 环境，若启动失败说明 conda 不在系统环境中...
    call activate videolingo
    python -m streamlit run st.py
    call deactivate
)

pause
