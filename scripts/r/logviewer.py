import argparse
import subprocess

from utils.menu.logviewer import LogViewerMenu

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", default=None, type=str)
    parser.add_argument("-f", "--filter", type=str, default=None)
    parser.add_argument("-c", "--cmdline", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    if args.cmdline:
        with open(args.file, "w") as f:
            ps = subprocess.Popen(args.cmdline, stdout=f, stderr=f)
            LogViewerMenu(file=args.file, filter=args.filter).exec()
            ps.wait()

    else:
        LogViewerMenu(file=args.file, filter=args.filter).exec()
