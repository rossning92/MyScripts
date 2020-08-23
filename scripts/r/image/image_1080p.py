from PIL import Image
from _shutil import *

OUT_SIZE = (1920, 1080)
files = get_files(cd=True)
files = [
    x for x in files if x.endswith(".jpg") or x.endswith(".png") or x.endswith(".bmp")
]

mkdir("out")
for f in files:
    fg = Image.open(f).convert("RGBA")

    if fg.width / fg.height > OUT_SIZE[0] / OUT_SIZE[1]:
        fg = fg.resize([OUT_SIZE[1] * fg.width // fg.height, OUT_SIZE[1]])
    else:
        fg = fg.resize([OUT_SIZE[0], OUT_SIZE[0] * fg.height // fg.width])

    bg = Image.new("RGB", (1920, 1080))

    bg.paste(fg, ((bg.width - fg.width) // 2, (bg.height - fg.height) // 2), fg)

    bg.save("out/" + f)
