import os
import subprocess
import sys

script_dir = os.getcwd()

def run_cmd(cmd, assert_success=False, environment=False, capture_output=False, env=None):
    # Use the conda environment
    if environment:
        conda_env_path = os.path.join(script_dir, "installer_files", "env")
        if sys.platform.startswith("win"):
            conda_bat_path = os.path.join(script_dir, "installer_files", "conda", "condabin", "conda.bat")
            cmd = "\"" + conda_bat_path + "\" activate \"" + conda_env_path + "\" >nul && " + cmd
        else:
            conda_sh_path = os.path.join(script_dir, "installer_files", "conda", "etc", "profile.d", "conda.sh")
            cmd = ". \"" + conda_sh_path + "\" && conda activate \"" + conda_env_path + "\" && " + cmd

    # Run shell commands
    result = subprocess.run(cmd, shell=True, capture_output=capture_output, env=env)

    # Assert the command ran successfully
    if assert_success and result.returncode != 0:
        print("Command '" + cmd + "' failed with exit status code '" + str(result.returncode) + "'. Exiting...")
        sys.exit()
    return result

def check_env():
    # If we have access to conda, we are probably in an environment
    conda_exist = run_cmd("conda", environment=True, capture_output=True).returncode == 0
    if not conda_exist:
        print("Conda is not installed. Exiting...")
        sys.exit()

    # safer environment check
    conda_env = os.environ.get("CONDA_DEFAULT_ENV")
    if conda_env is None:
        print("No conda environment is activated. Please check your conda installation. Exiting...")
        sys.exit()
    elif conda_env == "base":
        print("Create an environment for this project and activate it. Exiting...")
        sys.exit()

def install_dependencies():
    run_cmd("python install.py", assert_success=True, environment=True)

def run_model():
    run_cmd(f"python -m streamlit run st.py", environment=True)

if __name__ == "__main__":
    check_env()
    install_dependencies()
    run_model()