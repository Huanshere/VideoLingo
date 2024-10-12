@echo off
cd /d %~dp0
if exist runtime (
    echo Using runtime folder...
    runtime\python.exe -m streamlit run st.py
) else (
    echo Runtime folder not found. Using conda environment...
    call conda activate videolingo
    python -m streamlit run st.py
    call conda deactivate
)

pause