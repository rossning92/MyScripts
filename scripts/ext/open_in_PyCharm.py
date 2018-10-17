import glob
import subprocess
import os
import sys

# Get pycharm binary
files = glob.glob(r'C:\Program Files\JetBrains\**\pycharm64.exe', recursive=True) + glob.glob(
    r'C:\Program Files (x86)\JetBrains\**\pycharm64.exe', recursive=True)
if len(files) == 0:
    sys.exit(1)
pycharm = files[0]

if len(sys.argv) == 2:  # Open python file
    file = sys.argv[1]
    if os.path.exists(file):
        if os.path.splitext(file)[1] == '.py':
            subprocess.Popen([pycharm, file])
        elif os.path.isdir(file):
            subprocess.Popen([pycharm, file])
    else:
        raise Exception('Cannot find the file: %s' % file)

else:  # Open project folder
    project_folder = os.path.abspath(os.getcwd() + '/../../')
    subprocess.Popen([pycharm, project_folder])

subprocess.Popen(['AutoHotkeyU64.exe', '_activate_pycharm.ahk'])

sys.exit(0)
