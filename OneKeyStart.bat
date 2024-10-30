@echo off
cd /d %~dp0
if exist runtime (
    echo Using runtime folder...
    runtime\python.exe install.py
    runtime\python.exe -m streamlit run st.py
) else (
    echo Runtime folder not found. Using conda environment...
    call activate videolingo
    python install.py
    python -m streamlit run st.py
    call deactivate
)

pause