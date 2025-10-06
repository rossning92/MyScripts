import os
import sys

from _shutil import run_elevated
from utils.symlink import create_symlink


def _main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mpv_conf_dir = os.path.join(script_dir, "_mpv")

    if sys.platform == "win32":
        if not os.path.exists(os.path.expandvars("%APPDATA%\\mpv")):
            run_elevated(f'cmd /c MKLINK /D "%APPDATA%\\mpv" "{mpv_conf_dir}"')
    elif sys.platform == "linux":
        create_symlink(mpv_conf_dir, os.path.expanduser("~/.config/mpv"))


if __name__ == "__main__":
    _main()
