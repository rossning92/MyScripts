import os
import subprocess
from _cmake import setup_cmake
from _shutil import *

try:
    import _setup_android_env as android

    android.setup_android_env()
except:
    print('[WARNING] Android env not found.')

cd_current_dir()

setup_cmake()

subprocess.call(['cmd'])
