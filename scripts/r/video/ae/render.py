import argparse
import os

from _shutil import call_echo, find_newest_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str)
    args = parser.parse_args()

    aerender = find_newest_file(
        r"C:\Program Files\Adobe\Adobe After Effects*\Support Files\aerender.exe"
    )
    print(aerender)

    output = os.path.join(os.path.dirname(os.path.realpath(args.file)), "Comp1.avi")

    call_echo([aerender, "-project", args.file, "-comp", "Comp 1", "-output", output])
