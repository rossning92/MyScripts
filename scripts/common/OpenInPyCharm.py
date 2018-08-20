import glob
import subprocess
import os

os.chdir('../../')


files = glob.glob(r'C:\Program Files\JetBrains\**\pycharm64.exe', recursive=True)

assert len(files) > 0

subprocess.Popen([files[0], os.getcwd()])