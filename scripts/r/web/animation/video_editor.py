import sys
import subprocess
import threading
from _shutil import get_temp_file_name, getch, get_files, move_file
from _video import ffmpeg
from _term import SearchWindow


def edit_video(file):
    file_history = [file]

    class VideoEditorMenu(SearchWindow):
        def on_char(self, ch):
            if ch == ord("S"):
                move_file(file_history[-1], file_history[0], overwrite=True)
                sys.exit(0)

    while True:
        opt = VideoEditorMenu(items=["crop (0,0,1920,1080)"]).get_selected_index()

        if opt == 0:
            file_history.append(get_temp_file_name(".mp4"))

            ffmpeg(
                file_history[-2],
                out_file=file_history[-1],
                extra_args=["-filter:v", "crop=1920:1080:0:0"],
                quiet=True,
            )
            subprocess.call(["mpv", file_history[-1]])


if __name__ == "__main__":
    f = get_files()[0]

    edit_video(f)
