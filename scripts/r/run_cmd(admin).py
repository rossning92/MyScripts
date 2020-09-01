import os
import subprocess

if '_CUR_DIR' in os.environ:
    os.chdir(os.environ['_CUR_DIR'])
subprocess.Popen('cmd', close_fds=True)
