import os
import subprocess
import tempfile

from _pkgmanager import find_executable, require_package
from utils.shutil import shell_open

require_package("imagemagick")
IMAGE_MAGICK = find_executable("imagemagick")
os.environ["IMAGEMAGICK_BINARY"] = IMAGE_MAGICK


def render_text(
    text,
    font="Arial",
    font_size=45,
    color="#ffffff",
):
    from install_source_han_sans_sc import get_font_file

    font_file = get_font_file()

    text = text.replace("\\*", "*").replace("\\", "\\\\").replace("%", "%%")

    tempfile_fd, tempfilename = tempfile.mkstemp(suffix=".png")
    os.close(tempfile_fd)
    cmd = [
        IMAGE_MAGICK,
        "-background",
        "transparent",
        "-font",
        font_file.replace("\\", "/"),
        "-pointsize",
        "%d" % font_size,
        "-kerning",
        "%d" % int(font_size * 0.05),
        "-gravity",
        "center",
        "-fill",
        color,
        "label:%s" % text,
        "(",
        "+clone",
        "-background",
        "none",
        "-shadow",
        "100x4+0+4",
        ")",
        "+swap",
        "-background",
        "none",
        "-layers",
        "merge",
        "+repage",
        "PNG32:%s" % tempfilename,
    ]
    subprocess.check_call(cmd)
    return tempfilename


if __name__ == "__main__":
    f = render_text("中英文混排: Text / 文字!")
    shell_open(f)
