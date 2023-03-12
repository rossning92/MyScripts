import os
import subprocess
import sys

from _pkgmanager import find_executable
from _script import get_data_dir
from _shutil import setup_logger, start_process

if __name__ == "__main__":
    setup_logger()

    log_file = os.path.join(get_data_dir(), "MyScripts.log")
    klogg = find_executable("klogg")
    if klogg is not None:
        start_process([klogg, "--follow", log_file])
    elif sys.platform == "linux":
        subprocess.call(f"less -iNS +G +F '{log_file}'", shell=True)
