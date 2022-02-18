import os
import subprocess

from _appmanager import get_executable
from _script import get_data_dir

if __name__ == "__main__":
    log_file = os.path.join(get_data_dir(), "MyScripts.log")
    subprocess.check_call([get_executable("klogg"), log_file])
