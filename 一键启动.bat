@echo off
cd /d %~dp0
call runtime\Scripts\streamlit.exe run st.py
pause
