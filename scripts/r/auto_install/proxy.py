import os
import sys
import subprocess
from _config import *
from _shutil import run_elevated


def run_exe(exe, args):
    for p in os.getenv('PATH').split(os.pathsep):
        if p == BIN_PATH:
            continue

        exe_path = os.path.abspath(p + '/%s.exe' % exe)
        if os.path.exists(exe_path):
            print('Starting: %s' % exe_path)
            print('---')
            print()
            subprocess.call([exe_path] + args)
            return True

    return False


if __name__ == '__main__':
    # Set up PATH
    os.environ['PATH'] = os.pathsep.join([
        r'C:\Program Files\CMake\bin'
    ]) + os.pathsep + os.environ['PATH']

    exe = sys.argv[1]
    args = sys.argv[2:]
    if not run_exe(exe, args):
        # Install package
        run_elevated(['choco', 'install', CHOCO_PKG_MAP[exe], '-y'], wait=True)

        run_exe(exe, args)
