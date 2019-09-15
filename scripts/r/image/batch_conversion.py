from _shutil import *
from _image import *
import numpy as np

print2(os.environ['CURRENT_FOLDER'])

files = get_files(cd=True)

mkdir('out')

rect_arg = [float(x) for x in '{{_CROP_RECT}}'.split()]
scale = [float(x) for x in '{{_SCALE}}'.split()]
img_size = [int(x) for x in '{{_OUT_IMG_SIZE}}'.split()]
keep_ratio = bool('{{_KEEP_RATIO}}')

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
    elif len(img_size) == 2:
        if keep_ratio:
            aspect = im.size[0] / im.size[1]
            out_aspect = img_size[0] / img_size[1]
            if out_aspect > aspect:
                crop_rect = [0, 0, im.size[0], im.size[0] / out_aspect]
            else:
                crop_rect = [0, 0, im.size[1] * out_aspect, im.size[1]]
            print(crop_rect)
            im = crop_image(im, rect=crop_rect)

        im = im.resize((img_size[0], img_size[1]), Image.ANTIALIAS)

    name, ext = os.path.splitext(f)
    if '{{_OUT_FORMAT}}':
        ext = '.' + '{{_OUT_FORMAT}}'
    out_file = name + ext

    print('Output: out/' + out_file)
    im.save('out/' + out_file, quality=90)
