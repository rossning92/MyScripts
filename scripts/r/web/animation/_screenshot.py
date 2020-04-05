from mss import mss
from PIL import Image
from _shutil import *

SIZE = (1920, 1080)
TASKBAR_HEIGHT = 45

# The simplest use, save a screen shot of the 1st monitor
with mss() as sct:
    sct_img = sct.grab(sct.monitors[1])

    im_screencap = Image.frombytes(
        "RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")


im_screencap = im_screencap.resize(SIZE, resample=Image.BILINEAR)
im_screencap = im_screencap.crop((0, 0, SIZE[0], SIZE[1] - TASKBAR_HEIGHT))


im = Image.new(mode="RGB", size=SIZE)
im.paste(im_screencap, box=(0, TASKBAR_HEIGHT // 2))


os.makedirs('screenshot', exist_ok=True)
file_name = 'screenshot/%s.png' % get_time_str()
im.save(file_name)

clip = "<!--- image('%s') -->" % file_name
set_clip(clip)
print('Clip is set to: %s' + clip)
wait_key()
