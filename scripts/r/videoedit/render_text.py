from _pkgmanager import get_executable
from _shutil import shell_open
import tempfile
import os
import subprocess

IMAGE_MAGICK = get_executable("magick")
os.environ["IMAGEMAGICK_BINARY"] = IMAGE_MAGICK


def render_text(
    text,
    font="Arial",
    font_size=45,
    color="#ffffff",
    stroke_color="#000000",
):
    # Escape `%` in ImageMagick
    text = text.replace("\\*", "*").replace("\\", "\\\\").replace("%", "%%")

    # Generate subtitle png image using magick
    tempfile_fd, tempfilename = tempfile.mkstemp(suffix=".png")
    os.close(tempfile_fd)
    cmd = [
        IMAGE_MAGICK,
        "-background",
        "transparent",
        "-font",
        r"C:/Windows/Fonts/SourceHanSansSC-Bold.otf",
        "-pointsize",
        "%d" % font_size,
        "-stroke",
        stroke_color,
        "-strokewidth",
        "4",
        "-kerning",
        "%d" % int(font_size * 0.05),
        "-gravity",
        "center",
        "label:%s" % text,
        "-stroke",
        "None",
        "-fill",
        color,
        "label:%s" % text,
        "-layers",
        "merge",
        "PNG32:%s" % tempfilename,
    ]
    subprocess.check_call(cmd)
    return tempfilename


if __name__ == "__main__":
    f = render_text("中英文混排: Text / 文字!")
    shell_open(f)
