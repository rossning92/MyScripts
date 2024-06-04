import argparse
import os
import subprocess
import tempfile

from utils.menu.logviewer import LogViewerMenu
from utils.slugify import slugify

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", type=str)
    parser.add_argument("-o", "--output", type=str)
    parser.add_argument("-f", "--filter", type=str, default=None)
    parser.add_argument("-c", "--cmdline", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    preset_dir = os.environ.get("LOGVIEWER_PRESET_DIR")

    if args.cmdline:
        if args.output:
            file = args.output
        else:
            file = os.path.join(
                tempfile.gettempdir(), slugify(str(args.cmdline)) + ".log"
            )
        with open(file, "w") as f:
            ps = subprocess.Popen(args.cmdline, stdout=f, stderr=f)
            LogViewerMenu(
                files=[file],
                filter=args.filter,
                preset_dir=preset_dir,
            ).exec()
            ps.wait()

    else:
        LogViewerMenu(
            files=args.files,
            filter=args.filter,
            preset_dir=preset_dir,
        ).exec()
