import os

from _pkgmanager import find_executable, require_package
from _shutil import call_echo, get_files, mkdir

require_package("imagemagick")
magick = find_executable("imagemagick")
files = get_files()


for f in files:
    folder, basename = os.path.dirname(f), os.path.basename(f)
    name, ext = os.path.splitext(basename)
    if "{{_EXTENSION}}":
        ext = "{{_EXTENSION}}"

    args = [magick, f]

    if "{{_CROP_RECT}}":
        x, y, w, h = "{{_CROP_RECT}}".split()
        args += ["-crop", f"{w}x{h}+{x}+{y}"]

    if "{{_NEAREST}}":
        args += ["-filter", "point"]

    if "{{_FLIP}}":
        args += ["-flip"]

    if "{{_TRANSPARENT_COLOR}}":
        args += ["-transparent", "{{_TRANSPARENT_COLOR}}"]

    if "{{_TRIM}}":
        args += ["-trim", "+repage"]

    if "{{_RESIZE}}":
        args += ["-resize", "{{_RESIZE}}"]

    if "{{_AUTO_PAD}}":
        args += ["-gravity", "center", "-background", "black", "-extent", "{{_RESIZE}}"]
    elif "{{_AUTO_CROP}}":
        args += ["-gravity", "center", "-crop", "{{_RESIZE}}"]

    if "{{_BRIGHTNESS}}":
        args += ["-brightness-contrast", "{{_BRIGHTNESS}}x0"]

    out_file = os.path.join(folder, "out", "%s%s" % (name, ext))
    mkdir(os.path.join(folder, "out"))

    args += [f"{'PNG24:' if ext.lower()=='png' else ''}" + out_file]

    call_echo(args, shell=False)
