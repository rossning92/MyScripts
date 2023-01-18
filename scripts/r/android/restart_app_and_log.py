import argparse
import logging

from _android import logcat, restart_app
from _shutil import setup_logger

if __name__ == "__main__":
    setup_logger(level=logging.DEBUG)

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pkg", type=str)
    args = parser.parse_args()

    restart_app(args.pkg)
    logcat(pkg=args.pkg)
