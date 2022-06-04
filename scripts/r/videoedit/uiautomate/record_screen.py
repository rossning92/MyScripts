import argparse
import glob
import os
import subprocess
import sys
import time
from tempfile import gettempdir

import keyboard
import pyautogui
from _script import get_variable, set_variable
from _shutil import (
    call_echo,
    get_next_file_name,
    get_temp_file_name,
    move_file,
    print2,
    slugify,
)
from _term import activate_cur_terminal, minimize_cur_terminal, set_term_title
from _video import ffmpeg
from audio.postprocess import loudnorm

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import threading
from functools import partial


class ScreenRecorder:
    def __init__(self):
        self.rect = None
        self.no_audio = False

    def start_record(self):
        raise NotImplementedError

    def stop_record(self):
        raise NotImplementedError

    def save(self, file):
        raise NotImplementedError


class CapturaScreenRecorder(ScreenRecorder):
    def __init__(self):
        super().__init__()

        self.tmp_file = os.path.join(gettempdir(), "screen-record.mp4")
        self.captura_ps = None
        self.loudnorm = False

    def start_record(self):
        if self.captura_ps is not None:
            return

        subprocess.call(
            "taskkill /f /im captura-cli.exe",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

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
        for line in self.captura_ps.stdout:
            line = line.decode(errors="ignore")
            if "Press p to pause or resume" in line:
                print2("Recording started.", color="green")
                break

        time.sleep(0.2)

    def stop_record(self):
        if self.captura_ps is None:
            return

        self.captura_ps.stdin.write(b"q")
        self.captura_ps.stdin.close()
        self.captura_ps.wait()
        print2("Recording stopped.", color="green")
        self.captura_ps = None

    def save(self, file):
        # Save file
        if os.path.exists(file):
            os.remove(file)

        if self.loudnorm:
            tmp_file = get_temp_file_name(".mp4")
            loudnorm(self.tmp_file, tmp_file)
            self.tmp_file = tmp_file

        move_file(self.tmp_file, file)


class ShadowPlayScreenRecorder(ScreenRecorder):
    def __init__(self):
        super().__init__()

    def start_record(self):
        pyautogui.hotkey("alt", "f9")
        time.sleep(0.5)  # purely estimated warm-up time

    def stop_record(self):
        pyautogui.hotkey("alt", "f9")
        time.sleep(0.5)

    def save(self, file):
        # Get recorded video files
        files = glob.glob(
            os.path.expandvars("%USERPROFILE%\\Videos\\**\\*.mp4"), recursive=True,
        )
        files = sorted(list(files), key=os.path.getmtime, reverse=True)
        in_file = files[0]

        if os.path.exists(file):
            os.remove(file)

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

        move_file(in_file, file)


class FfmpegScreenRecorder(ScreenRecorder):
    def __init__(self):
        super().__init__()

        self.tmp_file = os.path.join(gettempdir(), "screen-record.mp4")
        self.proc = None
        self.loudnorm = False

    def start_record(self):
        if self.proc is not None:
            return

        args = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "gdigrab",
            "-framerate",
            "60",
        ]

        if self.rect is not None:
            args += [
                "-offset_x",
                f"{self.rect[0]}",
                "-offset_y",
                f"{self.rect[1]}",
                "-video_size",
                f"{self.rect[2]}x{self.rect[3]}",
            ]

        args += [
            "-draw_mouse",
            "1",
            "-i",
            "desktop",
            "-c:v",
            "libx264",
            "-r",
            "60",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            "-y",
            self.tmp_file,
        ]

        self.proc = subprocess.Popen(args, stdin=subprocess.PIPE)
        print2("Recording started.", color="green")

    def stop_record(self):
        if self.proc is None:
            return

        self.proc.stdin.write(b"q")
        self.proc.stdin.close()
        self.proc.wait()
        print2("Recording stopped.", color="green")
        self.proc = None

    def save(self, file):
        # Save file
        if os.path.exists(file):
            os.remove(file)

        move_file(self.tmp_file, file)


recorder = FfmpegScreenRecorder()

_cur_file = None


def start_record(file, rect=(0, 0, 1920, 1080)):
    global _cur_file

    _cur_file = file
    recorder.rect = rect
    recorder.start_record()


def stop_record():
    time.sleep(2)
    recorder.stop_record()
    recorder.save(_cur_file)


def wait_multiple_keys(keys):
    lock = threading.Event()
    handlers = []

    pressed = None

    def key_pressed(key):
        nonlocal pressed
        pressed = key
        lock.set()

    for key in keys:
        handler = keyboard.add_hotkey(key, partial(key_pressed, key), suppress=True)
        handlers.append(handler)

    lock.wait()

    for handler in handlers:
        keyboard.remove_hotkey(handler)

    return pressed


def prompt_record_file_name():
    last_file_name = get_variable("LAST_SCREEN_RECORD_FILE_NAME")
    if last_file_name:
        default_file_name = get_next_file_name(last_file_name)
    else:
        default_file_name = None

    name = input("Input file name [%s]: " % str(default_file_name))
    if not name:
        name = default_file_name
    set_variable("LAST_SCREEN_RECORD_FILE_NAME", name)
    file = os.path.join(out_dir, "%s.mp4" % slugify(name))
    return file


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

    minimize_cur_terminal()

    while True:
        recorder.start_record()

        pressed = wait_multiple_keys(["f6", "f7"])
        if pressed == "f6":
            print2("Canceling record...")
            recorder.stop_record()
            continue

        elif pressed == "f7":
            print2("Stoping record...")
            recorder.stop_record()
            break

    activate_cur_terminal()
    file = prompt_record_file_name()
    recorder.save(file)

    # Open file
    call_echo(["mpv", file])

    time.sleep(1)
