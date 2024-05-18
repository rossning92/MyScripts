import argparse
import os

from _image import crop_image, select_roi
from PIL import Image


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", help="input image files")
    args = parser.parse_args()

    rect = None
    for i, file in enumerate(args.files):
        im = Image.open(file)

        out_dir = os.path.join(os.path.dirname(file), "out")
        os.makedirs(out_dir, exist_ok=True)

        if i == 0:
            rect = select_roi(file)
            if rect is None:
                return

        im = crop_image(im, rect=rect)

        out_file = os.path.join(out_dir, os.path.basename(file))
        im.save(out_file, quality=90)


if __name__ == "__main__":
    _main()
