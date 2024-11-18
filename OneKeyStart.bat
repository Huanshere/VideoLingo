@echo off
cd /D "%~dp0"

set INSTALL_ENV_DIR=%cd%\installer_files\env
set CONDA_ROOT_PREFIX=%cd%\installer_files\conda

@rem Check if conda environment exists
if not exist "%INSTALL_ENV_DIR%\python.exe" (
    echo Conda environment not found!
    echo Please run OneKeyInstall^&Start.bat first to set up the environment.
    goto end
)

@rem Environment isolation
set PYTHONNOUSERSITE=1
set PYTHONPATH=
set PYTHONHOME=
set "CUDA_PATH=%INSTALL_ENV_DIR%"
set "CUDA_HOME=%CUDA_PATH%"

@rem Activate conda environment and run streamlit
call "%CONDA_ROOT_PREFIX%\condabin\conda.bat" activate "%INSTALL_ENV_DIR%" && (
    python -m streamlit run st.py
) || (
    echo Failed to activate conda environment!
    echo Please run OneKeyInstall^&Start.bat to reinstall the environment.
)

:end
pause 