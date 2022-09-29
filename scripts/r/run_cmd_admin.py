import os
import subprocess

if "CWD" in os.environ:
    os.chdir(os.environ["CWD"])
subprocess.Popen("cmd", close_fds=True)
