from _shutil import *
from _image import *
import numpy as np


def crop_border2(pil_image):
    np_array = np.array(pil_image)
    blank_px = [255, 255, 255, 0]
    mask = np_array != blank_px
    coords = np.argwhere(mask)
    x0, y0, z0 = coords.min(axis=0)
    x1, y1, z1 = coords.max(axis=0) + 1
    cropped_box = np_array[x0:x1, y0:y1, z0:z1]
    pil_image = Image.fromarray(cropped_box, "RGBA")
    return pil_image


def crop_border(pil_image):
    imageBox = pil_image.getbbox()
    pil_image = pil_image.crop(imageBox)
    return pil_image


def resize(im, w=None, h=None):
    if (w is None) and (h is not None):
        w = round(h * im.width / im.height)
    elif (w is not None) and (h is None):
        h = round(w * im.height / im.width)
    elif (w is None) and (h is None):
        raise Exception("w and h cannot be both None")

    return im.resize((w, h), resample=Image.LANCZOS)


rect_arg = [float(x) for x in "{{_CROP_RECT}}".split()]
scale = [float(x) for x in "{{_SCALE}}".split()]
img_size = [int(x) for x in "{{_OUT_IMG_SIZE}}".split()]
keep_ratio = bool("{{_KEEP_RATIO}}")


files = get_files(cd=True)
files = [
    x for x in files if x.endswith(".jpg") or x.endswith(".png") or x.endswith(".bmp")
]

crop = False
mkdir("out")
for f in files:
    im = Image.open(f)

    if "{{_SELECT_CROP_RECT}}" and not crop:
        box = select_roi2(f)
        rect = box
        rect_normalized = None
        crop = True
    else:
        if len(rect_arg) == 4:
            rect_normalized = None
            if (np.array(rect_arg) <= 1.0).all():
                rect_normalized = rect_arg
                rect = None
            else:
                rect = rect_arg
                rect_normalized = None
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

    if "{{_CROP_BORDER}}":
        im = crop_border(im)

    if "{{_DRAW_LABEL}}":
        s = os.path.splitext(os.path.basename(f))[0]
        arr = s.replace("_", " ").split()
        if arr[0].isdigit():
            del arr[0]
        s = " ".join(arr)
        draw_text(im, s)

    w = None
    h = None
    if "{{_RESIZE_W}}":
        w = int("{{_RESIZE_W}}")
    if "{{_RESIZE_H}}":
        h = int("{{_RESIZE_H}}")
    if w is not None or h is not None:
        im = resize(im, w=w, h=h)

    name, ext = os.path.splitext(f)
    if "{{_OUT_FORMAT}}":
        ext = "." + "{{_OUT_FORMAT}}"
    out_file = name + ext

    print("Output: out/" + out_file)
    im.save("out/" + out_file, quality=90)
