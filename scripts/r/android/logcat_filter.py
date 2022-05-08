from _android import logcat
from _shutil import call2
import argparse

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

    args = parser.parse_args()

    call2("adb wait-for-device")

    regex = args.regex if args.regex else r"{{_REGEX}}"
    pkg = args.pkg if args.pkg else r"{{_PKG}}"
    logcat(regex=regex, ignore_duplicates=False, pkg=pkg)
