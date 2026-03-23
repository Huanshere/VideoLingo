@echo off
cd /D "%~dp0"

:: Log file with timestamp
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set dt=%%I
set LOGFILE=videolingo_%dt:~0,8%_%dt:~8,6%.log

echo [%date% %time%] VideoLingo starting... > "%LOGFILE%"
echo Log file: %LOGFILE%

if exist ".venv\Scripts\streamlit.exe" (
    .venv\Scripts\streamlit run st.py 2>&1 | powershell -Command "$input | Tee-Object -FilePath '%LOGFILE%' -Append"
) else if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python -m streamlit run st.py 2>&1 | powershell -Command "$input | Tee-Object -FilePath '%LOGFILE%' -Append"
) else (
    echo ERROR: .venv not found. Please run setup first: | powershell -Command "$input | Tee-Object -FilePath '%LOGFILE%' -Append"
    echo   python setup_env.py
)
pause
