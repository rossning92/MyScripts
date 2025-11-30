import argparse
import os

from utils.remoteshell import push_file_ssh

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", type=str, nargs="*")
    args = parser.parse_args()

    if args.files:
        files = args.files
    else:
        files = [os.environ["SSH_FILE_TO_PUSH"]]

    user = os.environ["SSH_USER"]
    dest = os.environ.get("SSH_DEST", f"/home/{user}") 
    push_file_ssh(
        files,
        dest=dest,
        host=os.environ["SSH_HOST"],
        user=user,
        pwd=os.environ["SSH_PWD"],
        port=os.environ.get("SSH_PORT"),
    )
