import argparse
import os

from _shutil import cd
from utils.remoteshell import pull_file_ssh

if __name__ == "__main__":
    # Prerequisite: SSH_HOST, SSH_USER, SSH_PWD
    parser = argparse.ArgumentParser()
    parser.add_argument("src", type=str, nargs="?", default=None)
    args = parser.parse_args()

    if args.src:
        src = args.src
    else:
        src = os.environ["_SRC_FILE"]

    cd("~/Downloads")
    pull_file_ssh(src)
