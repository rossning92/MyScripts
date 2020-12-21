import sys
import subprocess
import threading
from _shutil import get_temp_file_name, getch, get_files, move_file
from _video import ffmpeg
from _term import Menu


def edit_video(file):
    file_history = [file]

    class VideoEditorMenu(Menu):
        def on_char(self, ch):
            if ch == ord("S"):
                move_file(file_history[-1], file_history[0], overwrite=True)
                sys.exit(0)

    while True:
        i = VideoEditorMenu(
            items=["crop 1920x1080", "crop 1440x810",]
        ).get_selected_index()

        if i in [0, 1]:
            file_history.append(get_temp_file_name(".mp4"))
            crop_params = {0: "crop=1920:1080:0:0", 1: "crop=1440:810:0:0"}

            ffmpeg(
                file_history[-2],
                out_file=file_history[-1],
                extra_args=["-filter:v", crop_params[i]],
                quiet=True,
            )
            subprocess.call(["mpv", file_history[-1]])
        elif 

if __name__ == "__main__":
    f = get_files()[0]

    edit_video(f)
