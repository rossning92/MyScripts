import argparse
import os

from _pkgmanager import find_executable, require_package
from _shutil import call2, mkdir, shell_open


def unzip(src, dest=None, open_out_dir=False):
    extracted = False
    for file in src:
        gzip_extension = [".tar.gz", ".tgz", ".gz"]
        for ext in gzip_extension:
            if file.endswith(ext):
                if dest:
                    out_dir = dest
                else:
                    out_dir = file.rstrip(ext)
                    mkdir(out_dir)
                call2(["tar", "xzvf", file, "-C", out_dir])
                extracted = True
                break

        if not extracted:
            require_package("7z")
            _7z = find_executable("7z")
            if dest:
                out_dir = dest
            else:
                out_dir = os.path.splitext(file)[0]
            args = [
                _7z,
                "x",  # extract
                "-aoa",  # overwrite all existing files
                "-o" + out_dir,  # out folder
                file,
            ]
            call2(args)

    if open_out_dir:
        shell_open(out_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("src", type=str)
    parser.add_argument("dest", type=str, nargs="?")
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()

    unzip([args.src], args.dest, open_out_dir=args.open)
