import subprocess
import os
import glob

os.chdir(r'{{UE_SOURCE}}\{{UE4_PROJECT_NAME}}\Binaries\Win64')

# Run last modified exe file in this folder
files = glob.glob("*.exe")
files = sorted(files, key=lambda x: os.path.getmtime(x), reverse=True)
binary_file = files[0]
print('Start %s ...' % binary_file)
subprocess.Popen(binary_file)
