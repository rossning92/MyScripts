import os
import subprocess
import sys
import locale

os.chdir(os.environ['CURRENT_FOLDER'])
if 'SELECTED_FILE' in os.environ:
    files = [os.path.basename(os.environ['SELECTED_FILE'])]
else:
    files = os.listdir('.')

for f in files:
    if not os.path.isfile(f):
        continue

    name_no_ext = os.path.splitext(f)[0]

    os.makedirs(name_no_ext, exist_ok=True)

    args = f'ffmpeg -i "{f}" -r 60 {name_no_ext}/Frame_%04d.bmp'
    subprocess.call(args)
