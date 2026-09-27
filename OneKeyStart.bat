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

if not exist "logs" mkdir "logs"
for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "dt=%%I"
set "LOGFILE=logs\videolingo_%dt%.log"
set "CHECK_ONLY="
if /I "%~1"=="--check-only" set "CHECK_ONLY=1"

> "%LOGFILE%" echo [%DATE% %TIME%] VideoLingo starting...
echo %C_CYAN%Log file:%C_RESET% %LOGFILE%

rem Install uv into the user's executable directory so uv run works in new terminals.
where uv >nul 2>nul
if errorlevel 1 (
    if defined CHECK_ONLY goto uv_ready
    echo %C_YELLOW%Installing uv for this user...%C_RESET%
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; irm https://astral.sh/uv/install.ps1 | iex"
    if errorlevel 1 goto install_failed
)
:uv_ready
if exist "%USERPROFILE%\.local\bin\uv.exe" set "PATH=%USERPROFILE%\.local\bin;%PATH%"

set "SHARED_VENV=%USERPROFILE%\.venvs\videolingo"
if exist "%SHARED_VENV%\Scripts\python.exe" (
    "%SHARED_VENV%\Scripts\python.exe" -c "import sys; sys.exit(sys.version_info[:2] != (3, 12))" >nul 2>nul
    if not errorlevel 1 (
        set "VENV_LABEL=shared venv"
        set "VENV_PY=%SHARED_VENV%\Scripts\python.exe"
        goto venv_found
    )
)

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import sys; sys.exit(sys.version_info[:2] != (3, 12))" >nul 2>nul
    if not errorlevel 1 (
        set "VENV_LABEL=project .venv"
        set "VENV_PY=.venv\Scripts\python.exe"
        goto venv_found
    )
)

rem Preserve an existing Conda installation before creating a new environment.
where conda >nul 2>nul
if not errorlevel 1 (
    call conda activate videolingo
    if not errorlevel 1 if /I "!CONDA_DEFAULT_ENV!"=="videolingo" (
        python -c "import sys; sys.exit(sys.version_info[:2] != (3, 12))" >nul 2>nul
        if not errorlevel 1 (
            set "VENV_LABEL=Conda"
            set "VENV_PY=python"
            goto env_found
        )
    )
)

if defined CHECK_ONLY (
    echo %C_RED%ERROR: No usable VideoLingo environment found.%C_RESET%
    exit /b 1
)

echo %C_YELLOW%First run: installing VideoLingo. This needs an internet connection...%C_RESET%
where uv >nul 2>nul
if errorlevel 1 goto install_failed
uv run --no-project --python 3.12 setup_env.py --yes
if errorlevel 1 goto install_failed
if not exist ".venv\Scripts\python.exe" goto install_failed
set "VENV_LABEL=project .venv"
set "VENV_PY=.venv\Scripts\python.exe"

:venv_found
for %%I in ("%VENV_PY%") do set "PATH=%%~dpI;%PATH%"

:env_found
echo %C_GREEN%Detected %VENV_LABEL%:%C_RESET% %VENV_PY%
if defined CHECK_ONLY (
    "%VENV_PY%" installer.py --check --quiet
    exit /b !errorlevel!
)

rem Metadata and file checks stay fast; a failed check enters the full repair path.
"%VENV_PY%" installer.py --quick-check --quiet
if errorlevel 1 (
    echo %C_YELLOW%Environment needs repair. Installing missing or changed components...%C_RESET%
    "%VENV_PY%" installer.py --yes
    if errorlevel 1 goto install_failed
)

echo %C_GREEN%Starting VideoLingo with %VENV_LABEL%...%C_RESET%
"%VENV_PY%" -m streamlit run st.py 2>&1 | powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\streamlit-log.ps1"
goto end

:install_failed
echo %C_RED%Install/repair failed. Check the messages above and the log file.%C_RESET%
echo Double-click OneKeyStart.bat again to retry.
pause
exit /b 1

:end
pause
