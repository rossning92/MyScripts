import os
import subprocess
from _cmake import setup_cmake
from _shutil import *
from _setup_android_env import *

try:
    setup_android_env()
except Exception as e:
    print2('ERROR: ' + str(e), color='red')

cd_current_dir()

setup_cmake()

setup_nodejs()

subprocess.call(['cmd'])
