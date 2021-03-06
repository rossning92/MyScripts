import subprocess
import sys
import os

script_path = os.environ['_SCRIPT']
script_dir = os.path.dirname(script_path)
os.chdir(script_dir)
print('Open Folder: ' + os.getcwd())

if sys.platform == 'darwin':
    subprocess.call('open .', shell=True)
elif sys.platform == 'win32':
    subprocess.call(['cmd', '/c', 'start', '', os.getcwd()])
elif sys.platform == 'linux':
    subprocess.call(['xdg-open', '.'])
