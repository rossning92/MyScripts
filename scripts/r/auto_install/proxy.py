import os
import sys
import subprocess
from _config import *
from _shutil import run_elevated


def run_exe(exe):
    for p in os.getenv('PATH').split(os.pathsep):
        if p == BIN_PATH:
            continue

        exe_path = os.path.abspath(p + '/%s.exe' % exe)
        if os.path.exists(exe_path):
            print('Starting: %s' % exe_path)
            subprocess.call(exe_path)
            return True

    return False


exe = sys.argv[1]
if not run_exe(exe):
    # Install package
    run_elevated(['choco', 'install', CHOCO_PKG_MAP[exe], '-y'], wait=True)

    run_exe(exe)
