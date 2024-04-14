import os

from _shutil import get_files
from _video import ffmpeg
from utils.logger import setup_logger
from utils.slugify import slugify

if __name__ == "__main__":
    setup_logger()
    in_file = get_files(cd=True)[0]
    name, ext = os.path.splitext(in_file)

    ext = ".mp4"

    start, duration = "{{_START_AND_DURATION}}".split()
    out_file = name + f"_cut_{slugify(start)}_{slugify(duration)}" + ext

    ffmpeg(
        in_file, out_file, start=float(start), duration=float(duration), reencode=True
    )
