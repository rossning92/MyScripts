import argparse

from _shutil import get_files
from ext.run_script_ssh import push_file_putty

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "file",
        type=str,
        default=None,
    )
    args = parser.parse_args()

    if args.file:
        file = args.file
    else:
        file = get_files()[0]

    push_file_putty(file)
