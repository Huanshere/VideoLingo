@echo off
cd /d %~dp0
runtime\python.exe -m streamlit run st.py
pause