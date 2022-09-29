import os
import subprocess
import sys
import locale
from _shutil import *


def extract_frames(file, fps=60):
    name_no_ext = os.path.splitext(file)[0]

    os.makedirs(name_no_ext, exist_ok=True)

    args = f'ffmpeg -i "{file}" -r {fps} -qscale:v 2 {name_no_ext}/%04d.jpg -hide_banner'
    subprocess.call(args)


if __name__ == '__main__':
    fps = int('{{_FPS}}') if '{{_FPS}}' else 60

    files = get_files(cd=True)

    for f in files:
        if not os.path.isfile(f):
            continue

        extract_frames(f, fps=fps)
