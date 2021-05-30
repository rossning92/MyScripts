from mss import mss
from PIL import Image
from _shutil import *
from _term import *
from _image import *

SIZE = (1920, 1080)
TASKBAR_HEIGHT = 45


def print_help():
    print2("[c] crop (0,0,1920,1080)\n" "[1] scale to 1080p\n" "[q] quit\n")


if __name__ == "__main__":
    os.chdir(os.environ["VIDEO_PROJECT_DIR"])

    # The simplest use, save a screen shot of the 1st monitor
    with mss() as sct:
        sct_img = sct.grab(sct.monitors[1])

        im = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

    activate_cur_terminal()
    name = input("screenshot name (no extension): ")
    os.makedirs("screencap", exist_ok=True)
    f = "screencap/%d-%s.png" % (int(time.time()), slugify(name))
    im.save(f)

    print_help()
    while True:
        ch = getch()
        if ch == "1":
            print("Scaling to 1080p")
            resize_image(f, 1920, 1080)
        elif ch == "q":
            break
        elif ch == "h":
            print_help()
