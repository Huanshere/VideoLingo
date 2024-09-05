@echo off
cd /d %~dp0
call .venv\Scripts\activate
call streamlit run st.py
pause