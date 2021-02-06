import os
import sys
import subprocess
from _config import *

proxy_path = os.path.abspath(os.getcwd() + '/proxy.py')
os.makedirs(BIN_PATH, exist_ok=True)

os.chdir(BIN_PATH)

for k, v in CHOCO_PKG_MAP.items():
    subprocess.call([
        'cmd2exe', '-o', '%s.exe' % k,
        '-c', 'python', proxy_path, k
    ])