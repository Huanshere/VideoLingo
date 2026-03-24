@echo off
cd /D "%~dp0"
cd ..

if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python batch\utils\batch_processor.py
) else (
    echo ERROR: .venv not found. Please run setup first:
    echo   python setup_env.py
    echo.
)

:end
pause
