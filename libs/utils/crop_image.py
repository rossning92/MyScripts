import argparse
import subprocess
from typing import Tuple


def crop_image(file_path, rect: Tuple[int, int, int, int], out_file):
    x, y, w, h = rect
    args = ["magick", file_path, "-crop", f"{w}x{h}+{x}+{y}", out_file]
    subprocess.check_call(args)


def _main():
    parser = argparse.ArgumentParser(description="Crop an image using ImageMagick.")
    parser.add_argument("file_path", type=str, help="Path to the input image file.")
    parser.add_argument(
        "-o",
        "--out_file",
        type=str,
        required=True,
        help="Path to the output cropped image file.",
    )
    parser.add_argument("rect", type=str, help="Cropping rect in the form 'x,y,w,h'.")

    args = parser.parse_args()

    crop_image(
        file_path=args.file_path,
        rect=map(int, args.rect.split(",")),
        out_file=args.out_file,
    )


if __name__ == "__main__":
    _main()
