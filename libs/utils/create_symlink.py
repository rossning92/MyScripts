import os
import sys

from .run_elevated import run_elevated


def create_symlink(src: str, dest: str):
    if os.path.exists(dest):
        os.remove(dest)
    if sys.platform == "win32":
        run_elevated(["cmd", "/c", "mklink", "/j", dest, src])
    else:
        os.symlink(src, dest)
