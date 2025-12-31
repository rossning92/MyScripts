import argparse
import os

from utils.editor import edit_text

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch rename files")
    parser.add_argument("files", nargs="+", help="Files to rename")
    args = parser.parse_args()

    files = sorted(args.files)

    common_dir = os.path.commonpath(files)
    if common_dir in files or not os.path.isdir(common_dir):
        common_dir = os.path.dirname(common_dir)

    if common_dir and common_dir != ".":
        os.chdir(common_dir)
        files = [os.path.relpath(f, common_dir) for f in files]

    s = "\n".join(files)
    s = edit_text(s)

    renamed_files = [x.strip() for x in s.splitlines()]

    for old, new in zip(files, renamed_files):
        if old != new:
            print("Rename %s => %s" % (old, new))
            os.rename(old, new)
