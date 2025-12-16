import argparse
import os
import subprocess
import tempfile

from utils.menu.logmenu import LogMenu
from utils.slugify import slugify

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", type=str)
    parser.add_argument("-o", "--output", type=str)
    parser.add_argument("-f", "--filter", type=str, default=None)
    parser.add_argument("-p", "--preset", type=str, default=None)
    parser.add_argument("--wrap-text", action="store_true")
    parser.add_argument("-c", "--cmdline", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    if args.cmdline:
        if args.output:
            file = args.output
        else:
            file = os.path.join(
                tempfile.gettempdir(), slugify(str(args.cmdline)) + ".log"
            )
        f = open(file, "w")
        subprocess.Popen(args.cmdline, stdout=f, stderr=f, stdin=subprocess.DEVNULL)
        files = [file]
    else:
        files = args.files

    LogMenu(
        files=files,
        filter=args.filter,
        wrap_text=args.wrap_text,
        preset_file=args.preset,
    ).exec()
