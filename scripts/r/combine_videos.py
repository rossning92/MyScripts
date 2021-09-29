import os

from _shutil import get_files
from _video import generate_video_matrix


if __name__ == "__main__":
    files = sorted(get_files(cd=True))

    titles = None
    if "{{_GEN_TITLES}}":
        titles = [os.path.splitext(x)[0] for x in files]

    crop_rect = [int(x) for x in "{{_CROP_RECT}}".split()] if "{{_CROP_RECT}}" else None

    generate_video_matrix(files, titles, "combined.mp4", crop_rect=crop_rect)
