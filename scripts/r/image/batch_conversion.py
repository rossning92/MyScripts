from _shutil import *
from _image import *
import numpy as np

print2(os.environ['CURRENT_FOLDER'])

files = get_files(cd=True)

mkdir('out')

rect_arg = [float(x) for x in '{{IMG_BATCH_CONV_RECT}}'.split()]
scale = [float(x) for x in '{{IMG_BATCH_CONV_SCALE}}'.split()]

crop = False
for f in files:
    im = Image.open(f)

    if '{{_SELECT_CROP_RECT}}' and not crop:
        box = select_region(f)
        rect = box
        rect_normalized = None
        crop = True
    else:
        if len(rect_arg) == 4:
            rect_normalized = None
            if (np.array(rect_arg) <= 1.0).all():
                rect_normalized = rect_arg
                rect = None
            crop = True

    if crop:
        im = crop_image(im, rect_normalized=rect_normalized, rect=rect)

    if len(scale) == 2:
        im = scale_image(im, scale[0], scale[1])

    print('Output: out/' + f)
    im.save('out/' + f, quality=100)
