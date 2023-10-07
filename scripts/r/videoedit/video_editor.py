import subprocess
import sys

from _shutil import get_files, get_temp_file_name, move_file
from _video import ffmpeg
from utils.menu import Menu


def edit_video(file):
    file_history = [file]

    def vfilter(params):
        file_history.append(get_temp_file_name(".mp4"))

        ffmpeg(
            file_history[-2],
            out_file=file_history[-1],
            extra_args=[
                "-filter:v",
                params,
            ],
            quiet=True,
        )
        subprocess.call(["mpv", file_history[-1]])

    class VideoEditorMenu(Menu):
        def on_char(self, ch):
            if ch == "S":
                move_file(file_history[-1], file_history[0], overwrite=True)
                sys.exit(0)

    while True:
        i = VideoEditorMenu(
            items=[
                "topLeft 1920x1080",
                "topLeft 1440x810",
                "bottomLeft 1920x1080",
                "crop left 1920x1080",
                "scale 1.5x",
            ]
        ).exec()

        if i == 0:
            vfilter("crop=1920:1080:0:0")
        elif i == 1:
            vfilter("crop=1440:810:0:0")
        elif i == 2:
            vfilter("crop=1920:1080:0:ih-1080")
        elif i == 3:
            vfilter("crop=1920:1080:0:(ih-1080)/2")
        elif i == 4:
            vfilter("scale=iw*1.5:ih*1.5")


if __name__ == "__main__":
    f = get_files()[0]

    edit_video(f)
