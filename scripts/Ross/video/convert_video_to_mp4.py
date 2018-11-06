import os
import subprocess
import sys
import locale

os.chdir(os.environ['CURRENT_FOLDER'])
files = os.listdir('.')

for f in files:
    if not os.path.isfile(f):
        continue

    name_no_ext = os.path.splitext(f)[0]
    out_file = 'out_%s.mp4' % name_no_ext

    args = [
        'ffmpeg',
        '-i', f,
        # '-filter:v', 'crop=200:200:305:86',
        # '-codec:v', 'libx264', '-preset', 'ultrafast', '-crf', '0',  # Lossless
        out_file
    ]
    subprocess.call(args)
