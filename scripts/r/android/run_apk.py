import argparse

from _android import run_apk, setup_android_env
from _shutil import setup_logger

if __name__ == "__main__":
    setup_logger()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file")
    args = parser.parse_args()
    apk = args.file

    setup_android_env()

    run_apk(apk)
