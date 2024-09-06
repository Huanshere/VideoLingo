@echo off
cd /d %~dp0
set PATH=%~dp0runtime;%PATH%
"%~dp0runtime\python.exe" -m streamlit run st.py
pause