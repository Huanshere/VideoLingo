@echo off
cd /d %~dp0
echo Warning: This batch file is only for one-click package, not for local installation.
runtime\python.exe -m streamlit run st.py
pause