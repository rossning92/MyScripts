import argparse
import os

from _android import logcat
from _shutil import call2

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pkg",
        default=None,
        type=str,
    )

    parser.add_argument(
        "-E",
        "--regex",
        default=None,
        type=str,
    )

    parser.add_argument(
        "--exclude",
        default=None,
        type=str,
    )

    args = parser.parse_args()

    call2("adb wait-for-device")

    if args.regex or args.pkg:
        regex = args.regex
        pkg = args.pkg
    else:
        regex = os.environ.get("_REGEX")
        pkg = os.environ.get("_PKG")

    while True:
        try:
            logcat(regex=regex, ignore_duplicates=False, pkg=pkg, exclude=args.exclude)
        except Exception:
            pass
