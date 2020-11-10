import os
import subprocess

if 'CUR_DIR_' in os.environ:
    os.chdir(os.environ['CUR_DIR_'])
subprocess.Popen('cmd', close_fds=True)
