@echo off
cd /d %~dp0
call .conda\Scripts\streamlit.exe run st.py
pause
