import os

from _pkgmanager import require_package
from _shutil import call2, call_echo, get_files

IMAGE_MAGICK = require_package("magick")
os.environ["IMAGEMAGICK_BINARY"] = IMAGE_MAGICK


from moviepy.editor import TextClip, VideoFileClip, clips_array


def add_caption(
    file,
    text,
    out_file=None,
    duration=None,
    fontsize=18,
):
    file = os.path.abspath(file)
    if out_file is None:
        d, f = os.path.dirname(file), os.path.basename(file)
        os.makedirs(os.path.join(d, "out"), exist_ok=True)
        out_file = os.path.join(d, "out", f)

    vid_clip = VideoFileClip(file)

    text_clip = TextClip(
        text,
        font="Verdana",
        fontsize=fontsize,
        color="white",
        size=(vid_clip.size[0], None),
        method="caption",
    ).set_duration(vid_clip.duration)

    final = clips_array([[vid_clip], [text_clip]]).set_mask(None)
    final = final.set_duration(duration if duration else vid_clip.duration)

    final.write_videofile(out_file)
    return out_file


if __name__ == "__main__":
    f = get_files(cd=True)[0]
    name_no_ext, ext = os.path.splitext(f)
    text_file = name_no_ext + ".txt"

    call2(["notepad.exe", text_file])
    with open(text_file, "r") as fp:
        text = fp.read()

    out_file = add_caption(f, text)
    call_echo([require_package("mpv"), out_file])
