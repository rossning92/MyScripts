from _shutil import *
from _video import *

fps = '{{_FPS}}' if '{{_FPS}}' else '60'

files = get_files(cd=True)

for f in files:
    if not os.path.isfile(f):
        continue

    fn, ext = os.path.splitext(f)
    out_file = '%s_out.mp4' % fn

    if '{{_480P}}':
        extra_args = ['-s', 'hd480', '-r', fps]
    elif '{{_720P}}':
        extra_args = ['-s', 'hd720', '-r', fps]
    else:
        extra_args = None

    ffmpeg(f, out_file=out_file, extra_args=extra_args, reencode=True)
