@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
set "PYTHONUTF8=1"
cd /D "%~dp0"

for /F "tokens=1,2 delims=#" %%A in ('"prompt #$H#$E# & echo on & for %%B in (1) do rem"') do set "ESC=%%B"
set "C_RESET=%ESC%[0m"
set "C_GREEN=%ESC%[32m"
set "C_YELLOW=%ESC%[33m"
set "C_RED=%ESC%[31m"
set "C_CYAN=%ESC%[36m"
set "C_BOLD=%ESC%[1m"

if not exist "logs" mkdir "logs"
for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "dt=%%I"
set "LOGFILE=logs\videolingo_%dt%.log"
set "CHECK_ONLY="
if /I "%~1"=="--check-only" set "CHECK_ONLY=1"

echo [%date% %time%] VideoLingo starting... > "%LOGFILE%"
echo %C_CYAN%Log file:%C_RESET% %LOGFILE%

set "VENV_LABEL="
set "VENV_PY="

set "SHARED_VENV=%USERPROFILE%\.venvs\videolingo"
if exist "%SHARED_VENV%\Scripts\python.exe" (
    set "VENV_LABEL=shared venv"
    set "VENV_PY=%SHARED_VENV%\Scripts\python.exe"
    goto venv_found
)

if exist ".venv\Scripts\python.exe" (
    set "VENV_LABEL=project .venv"
    set "VENV_PY=.venv\Scripts\python.exe"
    goto venv_found
)

where conda >nul 2>nul
if %errorlevel%==0 (
    echo %C_YELLOW%No uv venv found, falling back to Conda env "videolingo"...%C_RESET%
    call conda activate videolingo
    if errorlevel 1 (
        echo %C_RED%ERROR: Failed to activate Conda env "videolingo".%C_RESET%
        goto install_failed
    )
    if /I not "!CONDA_DEFAULT_ENV!"=="videolingo" (
        echo %C_RED%ERROR: Conda env "videolingo" is not active. Current env: !CONDA_DEFAULT_ENV!%C_RESET%
        goto install_failed
    )
    python installer.py --check --quiet
    if defined CHECK_ONLY exit /b !errorlevel!
    if errorlevel 1 (
        echo %C_YELLOW%Conda env is incomplete or outdated. Repairing...%C_RESET%
        python installer.py --yes
        if errorlevel 1 goto install_failed
    )
    if defined CHECK_ONLY (
        echo %C_GREEN%Environment check passed. --check-only set, not starting Streamlit.%C_RESET%
        goto end
    )
    echo %C_GREEN%Starting VideoLingo with Conda...%C_RESET%
    python -m streamlit run st.py 2>&1 | powershell -NoProfile -Command "$input | Tee-Object -FilePath '%LOGFILE%' -Append"
    goto end
)

echo %C_RED%ERROR: No usable VideoLingo environment found.%C_RESET%
echo Run one of these first:
echo   python setup_env.py --shared
echo   python setup_env.py
goto end

:venv_found
for %%I in ("%VENV_PY%") do set "PATH=%%~dpI;%PATH%"
echo %C_GREEN%Detected %VENV_LABEL%:%C_RESET% %VENV_PY%
"%VENV_PY%" installer.py --check --quiet
if defined CHECK_ONLY exit /b %errorlevel%
if errorlevel 1 (
    echo %C_YELLOW%Environment is incomplete or outdated. Repairing with installer.py...%C_RESET%
    "%VENV_PY%" installer.py --yes
    if errorlevel 1 goto install_failed
)

if defined CHECK_ONLY (
    echo %C_GREEN%Environment check passed. --check-only set, not starting Streamlit.%C_RESET%
    goto end
)

echo %C_GREEN%Starting VideoLingo with %VENV_LABEL%...%C_RESET%
"%VENV_PY%" -m streamlit run st.py 2>&1 | powershell -NoProfile -Command "$input | Tee-Object -FilePath '%LOGFILE%' -Append"
goto end

:install_failed
echo %C_RED%Install/repair failed. Check the messages above and the log file.%C_RESET%

:end
pause
