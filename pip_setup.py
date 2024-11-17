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

    # Ensure this is a new environment and not the base environment
    if os.environ["CONDA_DEFAULT_ENV"] == "base":
        print("Create an environment for this project and activate it. Exiting...")
        sys.exit()

def check_gpu_win():
    if not sys.platform.startswith('win'):
        return
    
    CUDNN_PATH = "C:\\Program Files\\NVIDIA\\CUDNN\\v9.3\\bin\\12.6"

    def check_gpu():
        try:
            subprocess.run(['nvidia-smi'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    if check_gpu():
        if CUDNN_PATH not in os.environ.get('PATH', ''):
            print("🚨 Warning: CUDNN path not found in system environment!")
            print(f"⚡ Please add the following path to system PATH:\n{CUDNN_PATH}")
            sys.exit(1)
        else:
            print("✅ CUDNN found in system PATH - All good!")

def install_dependencies():
    run_cmd("python install.py", assert_success=True, environment=True)

def run_model():
    run_cmd(f"python -m streamlit run st.py", environment=True)

if __name__ == "__main__":
    check_env()
    install_dependencies()
    check_gpu_win()
    run_model()
