import argparse
import os

from _shutil import cd
from ext.run_script_ssh import pull_file_putty

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("src", type=str, nargs="?", default=None)
    args = parser.parse_args()

    if args.src:
        src = args.src
    else:
        src = os.environ["_SRC_FILE"]

    cd("~/Downloads")
    pull_file_putty(src)
