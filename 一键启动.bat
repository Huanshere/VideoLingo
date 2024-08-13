@echo off
cd /d %~dp0
call runtime\python.exe -m streamlit run st.py
pause
