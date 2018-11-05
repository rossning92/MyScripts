import os
import subprocess
import sys
import locale

os.chdir(os.environ['CURRENT_FOLDER'])
files = os.listdir('.')

for f in files:
    if not os.path.isfile(f):
        continue

    out_file = 'out_' + f

    args = ['ffmpeg', '-i', f, out_file]
    subprocess.call(args)
