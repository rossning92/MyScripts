import argparse
import os

from PIL import Image


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()

    for file in args.files:
        if not file.endswith(".png"):
            im = Image.open(file).convert("RGBA")
            im.save(os.path.splitext(file)[0] + ".png")


if __name__ == "__main__":
    _main()
