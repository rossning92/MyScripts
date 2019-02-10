import os
import subprocess
import _setup_android_env

if 'CURRENT_FOLDER' in os.environ:
    os.chdir(os.environ['CURRENT_FOLDER'])
subprocess.Popen(['cmd'])
