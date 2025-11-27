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

    user = os.environ["SSH_USER"]
    push_file_ssh(
        file,
        dest=f"/home/{user}",
        host=os.environ["SSH_HOST"],
        user=user,
        pwd=os.environ["SSH_PWD"],
        port=os.environ.get("SSH_PORT"),
    )
