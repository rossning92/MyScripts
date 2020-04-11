from _shutil import *
from _video import *


crop_rect = [int(x)
             for x in '{{_CROP_RECT}}'.split()] if '{{_CROP_RECT}}' else None
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

    # TODO: merge to following filter_v
    # Scale (-2 indicates divisible by 2)
    if '{{_RESIZE_H}}':
        extra_args += ['-vf', 'scale=-2:{{_RESIZE_H}}']

    # Scale (-2 indicates divisible by 2)
    elif '{{_RESIZE_W}}':
        extra_args += ['-vf', 'scale={{_RESIZE_W}}:-2']

    filter_v = []

    # Crop video
    if crop_rect:
        filter_v.append(
            f'crop={crop_rect[2]}:{crop_rect[3]}:{crop_rect[0]}:{crop_rect[1]}')

    if '{{_TO_ANAMORPHIC}}':
        filter_v.append(
            'scale=1920:-2,crop=1920:816:0:132,pad=1920:1080:0:132')

    elif '{{_CROP_TO_1080P}}':
        filter_v.append(
            'scale=1920:-2,pad=1920:1080:0:0')

    if filter_v:
        extra_args += ['-filter:v', ','.join(filter_v)]

    # Cut video
    start_and_duration = None
    if '{{_START_AND_DURATION}}':
        start_and_duration = '{{_START_AND_DURATION}}'.split()

    # Pixel format
    extra_args += ['-pix_fmt', 'yuv420p']

    ffmpeg(
        f, out_file=out_file, extra_args=extra_args,
        reencode=True,
        crf=int('{{_CRF}}') if '{{_CRF}}' else None,
        start_and_duration=start_and_duration,
        nvenc=bool('{{_HW_ENC}}'),
        max_size_mb=float('{{_MAX_SIZE_MB}}') if '{{_MAX_SIZE_MB}}' else None,
        no_audio=bool('{{_NO_AUDIO}}')
    )
