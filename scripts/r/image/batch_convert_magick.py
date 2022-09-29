import os

from _pkgmanager import get_executable
from _shutil import call_echo, get_files, mkdir

magick = get_executable("magick")
files = get_files()


for f in files:
    folder, basename = os.path.dirname(f), os.path.basename(f)
    name, ext = os.path.splitext(basename)
    if "{{_EXT}}":
        ext = "{{_EXT}}"

    args = [magick, f]

    if "{{_CROP}}":
        x, y, w, h = "{{_CROP}}".split()
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

    out_file = os.path.join(folder, "out", "%s.%s" % (name, ext))
    mkdir(os.path.join(folder, "out"))

    args += [f"{'PNG24:' if ext.lower()=='png' else ''}" + out_file]

    call_echo(args, shell=False)
