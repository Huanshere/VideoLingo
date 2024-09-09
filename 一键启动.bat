@echo off
cd /d %~dp0
call activate videolingo
python -m streamlit run st.py
pause