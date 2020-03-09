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

    # FPS
    if '{{_FPS}}':
        extra_args += ['-r', '{{_FPS}}']

    # Scale (-2 indicates divisible by 2)
    if '{{_SCALE_H}}':
        extra_args += ['-vf', 'scale=-2:{{_SCALE_H}}']

    # Cut video
    start_and_duration = None
    if '{{_START_AND_DURATION}}':
        start_and_duration = '{{_START_AND_DURATION}}'.split()

    # Pixel format
    extra_args += ['-pix_fmt', 'yuv420p']

    ffmpeg(f, out_file=out_file, extra_args=extra_args,
           reencode=True, quality=quality,
           start_and_duration=start_and_duration,
           nvenc=bool('{{_HW_ENC}}'))