import argparse
import os

from _shutil import get_home_path
from utils.android import screenshot
from utils.logger import setup_logger
from utils.shutil import shell_open

# adb shell screencap -p /sdcard/screencap.png && adb pull /sdcard/screencap.png

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "out",
        nargs="?",
        default=None,
        type=str,
    )
    parser.add_argument(
        "-s",
        "--scale",
        default=(float(v) if (v := os.environ.get("SCREENSHOT_SCALE")) else None),
        type=float,
    )
    parser.add_argument(
        "--open",
        action="store_true",
    )
    args = parser.parse_args()

    setup_logger()

    if not args.out:
        os.chdir(os.path.join(get_home_path(), "Desktop"))

    file_name = screenshot(
        out_file=args.out if args.out else None,
        scale=args.scale,
    )

    if args.out is None or args.open:
        shell_open(file_name)
