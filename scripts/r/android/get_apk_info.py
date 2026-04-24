import argparse
import sys

from _shutil import call_echo, get_files
from utils.android import setup_android_env

# aapt dump badging xxx.apk


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="APK file path", nargs="?")
    args = parser.parse_args()

    if args.file:
        f = args.file
    else:
        f = get_files()[0]

    setup_android_env()
    call_echo(["aapt", "dump", "badging", f])
    call_echo(
        ["apksigner", "verify", "--print-certs", f], shell=sys.platform == "win32"
    )
