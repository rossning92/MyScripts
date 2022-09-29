from PIL import Image
from _shutil import *

OUT_SIZE = (1920, 1080)
files = get_files(cd=True)
files = [
    x for x in files if x.endswith(".jpg") or x.endswith(".png") or x.endswith(".bmp")
]


def paste_center(im, new_size):
    im = im.convert("RGBA")
    im_new = Image.new("RGB", new_size)
    im_new.paste(
        im, ((im_new.width - im.width) // 2, (im_new.height - im.height) // 2), im
    )
    return im_new


mkdir("out")
for f in files:
    fg = Image.open(f).convert("RGBA")

    if "{{_ANAMORPHIC}}":
        OUT_SIZE = (1920, 816)

    if "{{_RESIZE}}":
        if fg.width / fg.height > OUT_SIZE[0] / OUT_SIZE[1]:
            fg = fg.resize([OUT_SIZE[1] * fg.width // fg.height, OUT_SIZE[1]])
        else:
            fg = fg.resize([OUT_SIZE[0], OUT_SIZE[0] * fg.height // fg.width])

    bg = Image.new("RGB", OUT_SIZE)
    bg.paste(fg, ((bg.width - fg.width) // 2, (bg.height - fg.height) // 2), fg)

    bg = paste_center(fg, OUT_SIZE)

    bg = paste_center(bg, (1920, 1080))

    bg.save("out/" + f)
