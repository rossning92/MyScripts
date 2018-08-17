import subprocess
import sys
import os

os.chdir('../..')

script_path = os.environ['ROSS_SELECTED_SCRIPT_PATH']
script_dir = os.path.dirname(script_path)
os.chdir(script_dir)

if sys.platform == 'darwin':
    subprocess.call('open .', shell=True)
elif sys.platform == 'win32':
    subprocess.call('start .', shell=True)
