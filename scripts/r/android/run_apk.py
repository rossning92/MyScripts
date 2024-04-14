import argparse

from _android import run_apk, setup_android_env
from utils.logger import setup_logger

if __name__ == "__main__":
    setup_logger()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file")
    parser.add_argument("-p", "--grant_permissions", default=False, action="store_true")
    parser.add_argument("--force_reinstall", default=False, action="store_true")
    args = parser.parse_args()
    apk = args.file

    setup_android_env()

    run_apk(
        apk,
        grant_permissions=args.grant_permissions,
        force_reinstall=args.force_reinstall,
    )
