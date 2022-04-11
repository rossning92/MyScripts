from _shutil import get_files
from _video import hstack_videos

if __name__ == "__main__":
    files = sorted(get_files(cd=True))

    hstack_videos(files, out_file="output.mp4")
