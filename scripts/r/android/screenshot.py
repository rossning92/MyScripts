import argparse
import os

from _android import screenshot
from _shutil import get_home_path
from utils.logger import setup_logger
from utils.shutil import shell_open

# adb shell screencap -p /sdcard/screencap.png && adb pull /sdcard/screencap.png

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o",
        "--out",
        default=None,
        type=str,
    )
    args = parser.parse_args()

    setup_logger()

    if not args.out:
        os.chdir(os.path.join(get_home_path(), "Desktop"))

    n = int(os.environ.get("_COUNT", "1"))
    for i in range(n):
        file_name = screenshot(
            out_file=args.out if args.out else None,
            scale=float(os.environ["_SCALE"]) if os.environ.get("_SCALE") else None,
        )

    if args.out is None and n == 1:
        shell_open(file_name)
