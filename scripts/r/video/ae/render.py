from _shutil import *

import argparse


parser = argparse.ArgumentParser()
parser.add_argument("file", type=str)
args = parser.parse_args()

aerender = find_file(
    r"C:\Program Files\Adobe\Adobe After Effects*\Support Files\aerender.exe"
)
print(aerender)

output = os.path.join(os.path.dirname(os.path.realpath(args.file)), "Comp1.avi")

call_echo([aerender, "-project", args.file, "-comp", "Comp 1", "-output", output])

