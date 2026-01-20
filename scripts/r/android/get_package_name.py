import argparse
import re

from _shutil import check_output
from utils.android import setup_android_env

def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("apk", type=str)
    args = parser.parse_args()

    setup_android_env()
    out = check_output(["aapt", "dump", "badging", args.apk])
    pkg_name = re.findall(r"name='([\w.]+)", out)[0]
    print(pkg_name)


if __name__ == "__main__":
    _main()
