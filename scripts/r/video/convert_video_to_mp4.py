from _shutil import *
from _video import *

files = get_files(cd=True)

for f in files:
    if not os.path.isfile(f):
        continue

    fn, ext = os.path.splitext(f)
    out_file = '%s_out.mp4' % fn

    if '{{_480P}}':
        extra_args = ['-s', 'hd480']
    else:
        extra_args = None

    ffmpeg(f, out_file=out_file, extra_args=extra_args, reencode=True)
