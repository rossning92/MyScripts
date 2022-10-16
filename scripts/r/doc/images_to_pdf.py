import os

from _pkgmanager import find_executable
from _shutil import call_echo, get_files, setup_nodejs

if __name__ == "__main__":
    setup_nodejs()

    args = [find_executable("magick")]

    files = get_files(cd=True)
    args.extend(files)

    out_file_name = os.path.splitext(files[0])[0] + ".pdf"
    args.append(out_file_name)

    call_echo(args)
