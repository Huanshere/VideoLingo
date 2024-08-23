@echo off
cd /d %~dp0
call conda activate videolingo
call streamlit run st.py
pause