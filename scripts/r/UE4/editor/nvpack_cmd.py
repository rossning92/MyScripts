import os
import subprocess
import _setup_android_env; _setup_android_env.setup_android_env()
from _nvpack import *

setup_nvpack(r'{{NVPACK_ROOT}}')
os.chdir(os.environ['CUR_DIR_'])
subprocess.call('cmd /c start')
