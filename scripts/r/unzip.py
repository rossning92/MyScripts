import os

from _pkgmanager import require_package
from _shutil import call2, get_files, mkdir, shell_open


def unzip(files):
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
            _7z = require_package("7z")
            out_dir = os.path.splitext(file)[0]
            args = [
                _7z,
                "x",  # extract
                "-aoa",  # overwrite all existing files
                "-o" + out_dir,  # out folder
                file,
            ]
            call2(args)

    if len(files) == 1:
        shell_open(out_dir)


if __name__ == "__main__":
    files = get_files(cd=True)
    unzip(files)
