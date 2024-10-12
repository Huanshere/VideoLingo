@echo off
cd /d %~dp0
if exist runtime (
    echo 正在使用 runtime 文件夹环境...
    runtime\python.exe -m streamlit run st.py
) else (
    echo 未找到 runtime 文件夹。正在使用 conda 环境...
    call conda activate videolingo
    python -m streamlit run st.py
    call conda deactivate
)

pause
