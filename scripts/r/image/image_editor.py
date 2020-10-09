from mss import mss
from PIL import Image
from _shutil import *
from _term import *
from _image import *


def print_help():
    print2("[s] scale 2x\n" "[q] quit\n")


if __name__ == "__main__":
    f = get_files()[0]

    print_help()
    while True:
        ch = getch()
        if ch == "s":
            print("Scaling to 2x...")
            scale_image(f, 2, 2)
        elif ch == "q":
            break
        elif ch == "h":
            print_help()
