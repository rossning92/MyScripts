import argparse
import os

from _android import screenshot
from _shutil import setup_logger, shell_open

# adb shell screencap -p /sdcard/screencap.png
# adb pull /sdcard/screencap.png

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o",
        "--out",
    )
    args = parser.parse_args()

    setup_logger()

    os.chdir(os.path.expanduser("~/Desktop"))

    n = int(os.environ.get("_COUNT", "1"))
    for i in range(n):
        file_name = screenshot(
            out_file=args.out if args.out else None,
            scale=float(os.environ["_SCALE"]) if "_SCALE" in os.environ else None,
        )

    if args.out is None and n == 1:
        shell_open(file_name)
