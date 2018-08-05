import subprocess
import sys
import os

os.chdir('../..')

if sys.platform == 'darwin':
    subprocess.call('open .', shell=True)
elif sys.platform == 'win32':
    subprocess.call('start .', shell=True)
