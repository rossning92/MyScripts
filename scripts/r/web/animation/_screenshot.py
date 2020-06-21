from mss import mss
from PIL import Image
from _shutil import *
from _term import *

SIZE = (1920, 1080)
TASKBAR_HEIGHT = 45

# The simplest use, save a screen shot of the 1st monitor
with mss() as sct:
    sct_img = sct.grab(sct.monitors[1])

    im = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")


# im = im.resize(SIZE, resample=Image.BILINEAR)
# im = im.crop((0, 0, SIZE[0], SIZE[1] - TASKBAR_HEIGHT))


# im = Image.new(mode="RGB", size=SIZE)
# im.paste(im, box=(0, TASKBAR_HEIGHT // 2))


os.makedirs("screenshot", exist_ok=True)

activate_cur_terminal()
name = input("screenshot file name (no extension): ")
file = "screenshot/%s.png" % name
im.save(file)

clip = "{" + "{ image('%s') }}" % file
set_clip(clip)
print("Clip is set to: %s" % clip)
wait_key()
