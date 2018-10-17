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

# Open python file specified in command line argument
if len(sys.argv) == 2:
    arg1 = sys.argv[1]
    if os.path.exists(arg1):
        if os.path.splitext(arg1)[1] == '.py':
            subprocess.Popen([pycharm, arg1])
        elif os.path.isdir(arg1):
            subprocess.Popen([pycharm, arg1])
else:  # Open project folder
    os.chdir('../../')
    subprocess.Popen([pycharm, os.getcwd()])

ahk = os.path.join(os.path.dirname(__file__), '../../bin/AutoHotkeyU64.exe')
ahk = os.path.abspath(ahk)
script = os.path.join(os.path.dirname(__file__), '_activate_pycharm.ahk')
script = os.path.abspath(script)

subprocess.Popen([ahk, script])

sys.exit(0)
