from _video import *
from _shutil import *


fps = '{{_FPS}}' if '{{_FPS}}' else '60'

cd(os.environ['CURRENT_FOLDER'])

files = []
image_ext = None
for f in sorted(glob.glob('*')):
    ext = os.path.splitext(f)[1]
    if ext in ['.jpg', '.bmp', '.png']:
        files.append(f)
        image_ext = ext

# i = 1
# for f in files:
#     new_name = 'img%04d.bmp' % i
#     if f != new_name:
#         os.rename(f, new_name)
#     i += 1

ffmpeg(in_file='img%04d' + image_ext, extra_args=['-r', fps])
