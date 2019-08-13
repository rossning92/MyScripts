from _shutil import *
from _image import *
import numpy as np

files = get_files(cd=True)

mkdir('out')

rect = [float(x) for x in '{{IMG_BATCH_CONV_RECT}}'.split()]
scale = [float(x) for x in '{{IMG_BATCH_CONV_SCALE}}'.split()]

for f in files:
    im = Image.open(f)

    if len(rect) == 4:
        rect_normalized = None
        if (np.array(rect) <= 1.0).all():
            rect_normalized = rect
            rect = None

        im = crop_image(im, rect_normalized=rect_normalized, rect=rect)

    if len(scale) == 2:
        im = scale_image(im, scale[0], scale[1])

    print('Output: out/' + f)
    im.save('out/' + f, quality=100)
