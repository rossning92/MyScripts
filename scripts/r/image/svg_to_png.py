import os

from _pkgmanager import find_executable, require_package
from _shutil import call_echo, get_files

require_package("imagemagick")
magick = find_executable("magick")

f = get_files(cd=True)[0]
name, ext = os.path.splitext(f)

call_echo(
    [
        magick,
        "-density",
        "400",
        "-background",
        "None",
        f,
        "-resize",
        "x{{_RESIZE_HEIGHT}}",
        name + ".png",
    ]
)
