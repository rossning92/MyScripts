import os
import subprocess

from _pkgmanager import require_package
from _shutil import require_package, get_files

if __name__ == "__main__":
    mpv = require_package("mpv")
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
