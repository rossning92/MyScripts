import subprocess
import sys
import os

os.chdir('../..')

if sys.platform == 'darwin':
    subprocess.call('open .', shell=True)
