import argparse
import os

from utils.editor import edit_text

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch rename files")
    parser.add_argument("files", nargs="+", help="Files to rename")
    args = parser.parse_args()

    files = args.files
    files = sorted(files)

    s = "\n".join(files)
    s = edit_text(s)

    renamed_files = [x.strip() for x in s.splitlines()]

    for old, new in zip(files, renamed_files):
        if old != new:
            print("%s => %s" % (old, new))
            os.rename(old, new)
