@echo off
setlocal EnableExtensions
chcp 65001 >nul
set "PYTHONUTF8=1"
cd /D "%~dp0"
cd ..

set "VENV_PY=%USERPROFILE%\.venvs\videolingo\Scripts\python.exe"
if exist "%VENV_PY%" goto venv_found
set "VENV_PY=%CD%\.venv\Scripts\python.exe"
if exist "%VENV_PY%" goto venv_found

call conda activate videolingo
if errorlevel 1 goto failed
if /I not "%CONDA_DEFAULT_ENV%"=="videolingo" goto failed
set "VENV_PY=%CONDA_PREFIX%\python.exe"

:venv_found
for %%I in ("%VENV_PY%") do set "PATH=%%~dpI;%PATH%"
"%VENV_PY%" installer.py --check
if errorlevel 1 goto failed
"%VENV_PY%" batch\utils\batch_processor.py
goto end

:failed
echo ERROR: No healthy VideoLingo environment. Run setup_env.py or installer.py first.

:end
pause
