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
    arg1 = sys.argv[1]
    if os.path.exists(arg1):
        if os.path.splitext(arg1)[1] == '.py':
            subprocess.Popen([pycharm, arg1])
        elif os.path.isdir(arg1):
            subprocess.Popen([pycharm, arg1])

else:  # Open project folder
    project_folder = os.path.abspath(os.getcwd() + '/../../')
    subprocess.Popen([pycharm, project_folder])

subprocess.Popen(['AutoHotkeyU64.exe', '_activate_pycharm.ahk'])

sys.exit(0)
