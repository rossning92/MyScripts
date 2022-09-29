import os

from _shutil import get_files
from _video import generate_video_matrix

if __name__ == "__main__":
    files = sorted(get_files(cd=True))
    titles = (
        [os.path.splitext(x)[0] for x in files]
        if os.environ.get("_GEN_TITLES")
        else None
    )
    crop_rect = (
        [int(x) for x in os.environ["_CROP_RECT"].split()]
        if "_CROP_RECT" in os.environ
        else None
    )
    columns = int(os.environ["_COLUMNS"]) if "_COLUMNS" in os.environ else None

    generate_video_matrix(
        files, titles, "combined.mp4", crop_rect=crop_rect, columns=columns
    )
