import os
import subprocess
import _setup_android_env
from _nvpack import *

setup_nvpack()
os.chdir(os.environ['CURRENT_FOLDER'])
subprocess.call('cmd /c start')
