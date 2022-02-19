import os

from _appmanager import get_executable
from _script import get_data_dir
from _shutil import start_process

if __name__ == "__main__":
    log_file = os.path.join(get_data_dir(), "MyScripts.log")
    start_process([get_executable("klogg"), "--follow", log_file])
