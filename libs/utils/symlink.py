import os
import sys

from .run_elevated import run_elevated


def create_symlink(src: str, dest: str):
    if os.path.lexists(dest):
        if os.path.islink(dest):
            os.remove(dest)
        elif os.path.isdir(dest):
            print(f"Skipping: {dest} is a directory.")
            return
        else:
            os.remove(dest)
    if sys.platform == "win32":
        run_elevated(["cmd", "/c", "mklink", "/j", dest, src])
    else:
        os.symlink(src, dest)
