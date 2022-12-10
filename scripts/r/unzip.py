import os
import sys

from _pkgmanager import find_executable, require_package
from _shutil import call2, get_files, mkdir, shell_open


def unzip(files, open_out_dir=False):
    extracted = False
    for file in files:
        gzip_extension = [".tar.gz", ".tgz", ".gz"]
        for ext in gzip_extension:
            if file.endswith(ext):
                out_dir = file.rstrip(ext)
                mkdir(out_dir)
                call2(["tar", "xzvf", file, "-C", out_dir])
                extracted = True
                break

        if not extracted:
            require_package("7z")
            _7z = find_executable("7z")
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
    if len(sys.argv) == 2:
        file = sys.argv[1]
        unzip([file])
    else:
        files = get_files(cd=True)
        unzip(files, open_out_dir=len(files) == 1)
