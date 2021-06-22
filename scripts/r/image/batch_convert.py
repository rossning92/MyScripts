import os

from _appmanager import get_executable
from _shutil import call_echo, get_files, mkdir

magick = get_executable("magick")
files = get_files()


for f in files:
    folder, basename = os.path.dirname(f), os.path.basename(f)

    args = [magick, f]

    if "{{_TRANSPARENT_COLOR}}":
        args += ["-transparent", "{{_TRANSPARENT_COLOR}}"]

    if "{{_TRIM}}":
        args += ["-trim", "+repage"]

    if "{{_RESIZE}}":
        args += ["-resize", "{{_RESIZE}}"]

    out_file = os.path.join(folder, "out", basename)
    mkdir(os.path.join(folder, "out"))

    args += ["PNG24:" + out_file]

    call_echo(args, shell=False)
