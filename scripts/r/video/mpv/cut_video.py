import os
import subprocess

from _pkgmanager import find_executable, require_package
from _shutil import get_files

if __name__ == "__main__":
    require_package("mpv")
    mpv = find_executable("mpv")
    file = get_files(cd=True)[0]

    script = os.path.join(os.path.dirname(__file__), "excerpt.lua")
    subprocess.Popen(
        [
            "mpv",
            "--script=%s" % script,
            "--script-opts=osc-layout=bottombar",
            "--osd-font-size",
            "32",
            "--osd-scale-by-window=no",
            file,
        ]
    )
