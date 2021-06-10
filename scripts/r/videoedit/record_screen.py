import argparse
import glob
import os
import subprocess
import sys
import time

import keyboard
import pyautogui
from _shutil import (
    call_echo,
    get_temp_file_name,
    gettempdir,
    move_file,
    print2,
    slugify,
)
from _term import activate_cur_terminal, minimize_cur_terminal
from _video import ffmpeg
from audio.postprocess import loudnorm

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from video_editor import edit_video


class ScreenRecorder:
    def __init__(self):
        self.rect = None
        self.file = None
        self.no_audio = False


class CapturaScreenRecorder(ScreenRecorder):
    def __init__(self):
        super().__init__()

        self.tmp_file = os.path.join(gettempdir(), "screen-record.mp4")
        self.captura_ps = None
        self.file = None
        self.loudnorm = False

    def start_record(self):
        if self.captura_ps is not None:
            return

        # https://github.com/MathewSachin/Captura/tree/master/docs/Cmdline
        args = [
            "captura-cli",
            "start",
            "--speaker=4",
            "--cursor",
            "-r",
            "60",
            "--vq",
            "100",
            "-f",
            self.tmp_file,
            "-y",
        ]

        if self.rect is not None:
            args += [
                "--source",
                ",".join(["%d" % x for x in self.rect]),
            ]

        self.captura_ps = subprocess.Popen(
            args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        )
        print2("Recording started.", color="green")

    def stop_record(self):
        assert self.file

        self.captura_ps
        if self.captura_ps is None:
            return

        self.captura_ps.stdin.write(b"q")
        self.captura_ps.stdin.close()
        self.captura_ps.wait()
        print2("Recording stopped.", color="green")
        self.captura_ps = None

        # Save file
        if os.path.exists(self.file):
            os.remove(self.file)

        if self.loudnorm:
            tmp_file = get_temp_file_name(".mp4")
            loudnorm(self.tmp_file, tmp_file)
            self.tmp_file = tmp_file

        move_file(self.tmp_file, self.file)


class ShadowPlayScreenRecorder(ScreenRecorder):
    def __init__(self):
        super().__init__()

    def start_record(self):
        pyautogui.hotkey("alt", "f9")
        time.sleep(0.5)  # purely estimated warm-up time

    def stop_record(self):
        pyautogui.hotkey("alt", "f9")
        time.sleep(0.5)

        # Get recorded video files
        files = glob.glob(
            os.path.expandvars("%USERPROFILE%\\Videos\\**\\*.mp4"), recursive=True,
        )
        files = sorted(list(files), key=os.path.getmtime, reverse=True)
        in_file = files[0]

        if os.path.exists(self.file):
            os.remove(self.file)

        if self.rect is not None:
            out_file = get_temp_file_name(".mp4")
            ffmpeg(
                in_file,
                out_file=out_file,
                extra_args=[
                    "-filter:v",
                    "crop=%d:%d:%d:%d"
                    % (self.rect[2], self.rect[3], self.rect[0], self.rect[1]),
                ],
                quiet=True,
                no_audio=self.no_audio,
                nvenc=True,
            )
            os.remove(in_file)
            in_file = out_file

        move_file(in_file, self.file)


recorder = CapturaScreenRecorder()
recorder = ShadowPlayScreenRecorder()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rect", type=int, nargs="+", default=(0, 0, 1920, 1080))
    parser.add_argument("--no_audio", default=False, action="store_true")
    parser.add_argument("--out_dir", type=str, default=None)

    args = parser.parse_args()

    recorder.no_audio = args.no_audio

    if args.rect is not None:
        recorder.rect = args.rect

    if args.out_dir is None:
        out_dir = os.path.expanduser("~/Desktop")
    else:
        out_dir = args.out_dir

    name = input("input file name (no ext): ")
    if not name:
        sys.exit(0)

    recorder.file = os.path.join(out_dir, "%s.mp4" % slugify(name))
    recorder.start_record()
    minimize_cur_terminal()

    keyboard.wait("f6", suppress=True)
    recorder.stop_record()
    activate_cur_terminal()

    # Open file
    call_echo(["mpv", recorder.file])
    # edit_video(dst_file)

    time.sleep(1)
