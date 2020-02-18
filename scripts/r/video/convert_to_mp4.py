from _shutil import *
from _video import *


quality = '{{_QUALITY}}' if '{{_QUALITY}}' else 0

files = get_files(cd=True)

for f in files:
    if not os.path.isfile(f):
        continue

    fn, ext = os.path.splitext(f)
    out_file = '%s_out.mp4' % fn

    extra_args = []
    if '{{_FPS}}':
        extra_args += ['-r', '{{_FPS}}']

    if '{{_SCALE_H}}':
        extra_args += ['-vf', 'scale=-1:{{_SCALE_H}}']

    extra_args += ['-pix_fmt', 'yuv420p']

    ffmpeg(f, out_file=out_file, extra_args=extra_args,
           reencode=True, quality=quality)
