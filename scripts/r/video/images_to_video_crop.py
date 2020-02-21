from _video import *
import cv2
from _script import *

if '{{CROP_RECT}}':
    CROP_RECT = [int(x) for x in '{{CROP_RECT}}'.split()]
else:
    CROP_RECT = None

fps = int('{{IMG2VID_FPS}}') if '{{IMG2VID_FPS}}' else 30


def crop_image(im, rect):
    return im[rect[1]:rect[1] + rect[3], rect[0]:rect[0] + rect[2], :]


cur_folder = os.environ['CURRENT_FOLDER']
cd(cur_folder)

files = os.listdir('.')
files = [x for x in files if x.endswith(
    '.jpg') or x.endswith('.png') or x.endswith('.bmp')]
files = sorted(files)

if len(files) == 0:
    print('ERROR: no image files found.')
    sys.exit(1)

imgs = []
for i, f in enumerate(files):
    print('Processing (%d / %d)...' % (i, len(files)))
    im = cv2.imread(f)
    if CROP_RECT:
        im = crop_image(im, CROP_RECT)
    imgs.append(im)

make_video(imgs, out_file='out.mp4', fps=fps)
