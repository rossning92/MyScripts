import os
import subprocess
import sys
import locale
from _shutil import *

fps = int('{{VID_TO_IMG_FPS}}') if '{{VID_TO_IMG_FPS}}' else 60

files = get_files(cd=True)

for f in files:
    if not os.path.isfile(f):
        continue

    name_no_ext = os.path.splitext(f)[0]

    os.makedirs(name_no_ext, exist_ok=True)

    args = f'ffmpeg -i "{f}" -r {fps} -qscale:v 2 {name_no_ext}/%04d.jpg -hide_banner'
    subprocess.call(args)
