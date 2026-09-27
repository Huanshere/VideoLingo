@echo off
setlocal EnableExtensions
cd /D "%~dp0"
if errorlevel 1 goto failed

rem An existing installation can be checked and started by OneKeyStart.
if exist "%USERPROFILE%\.venvs\videolingo\Scripts\python.exe" goto start
if exist ".venv\Scripts\python.exe" goto start

where uv >nul 2>nul
if not errorlevel 1 goto install

rem Keep uv beside this checkout so users do not need to set up PATH.
if not exist ".tools\uv.exe" (
    echo Installing the setup tool. This needs an internet connection...
    set "UV_UNMANAGED_INSTALL=%CD%\.tools"
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; irm https://astral.sh/uv/install.ps1 | iex"
    if errorlevel 1 goto failed
)
set "PATH=%CD%\.tools;%PATH%"
where uv >nul 2>nul
if errorlevel 1 goto failed

:install
echo Installing VideoLingo. The first download may take a while...
uv run --no-project --python 3.13 setup_env.py
if errorlevel 1 goto failed

:start
call OneKeyStart.bat
exit /b %errorlevel%

:failed
echo.
echo Installation could not finish. Check the error above, then double-click OneKeyInstall.bat again.
pause
exit /b 1
