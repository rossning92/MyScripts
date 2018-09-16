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

# Open python file or project folder
print(len(sys.argv) == 2)
file = sys.argv[1]
if os.path.exists(file) and os.path.splitext(file)[1] == '.py':
    subprocess.Popen([pycharm, file])
else:
    os.chdir('../../')
    subprocess.Popen([pycharm, os.getcwd()])
sys.exit(0)
