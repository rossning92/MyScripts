import argparse
import os

from utils.remoteshell import push_file_ssh

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "file",
        type=str,
        nargs="?",
    )
    args = parser.parse_args()

    if args.file:
        file = args.file
    else:
        file = os.environ["SSH_FILE_TO_PUSH"]

    # Prerequisite: SSH_HOST, SSH_USER, SSH_PWD, SSH_PORT
    push_file_ssh(
        file,
        dest="/home/rossning92",
        host=os.environ.get("SSH_HOST"),
        user=os.environ.get("SSH_USER"),
        pwd=os.environ.get("SSH_PWD"),
    )
