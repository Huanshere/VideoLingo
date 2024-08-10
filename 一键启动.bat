@echo off
cd /d %~dp0
call .venv\Scripts\streamlit.exe run st.py
pause
