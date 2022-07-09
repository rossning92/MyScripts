import argparse
import ctypes
import ctypes.wintypes
import glob
import logging
import os
import subprocess
import sys
import time
from tempfile import gettempdir

import pyautogui
import pywinauto
from _script import get_variable, set_variable
from _shutil import (
    call_echo,
    get_next_file_name,
    get_temp_file_name,
    move_file,
    print2,
    slugify,
    start_process,
    wait_for_key,
)
from _term import activate_cur_terminal, minimize_cur_terminal
from _video import ffmpeg
from audio.postprocess import loudnorm
from pywinauto.application import Application

sys.path.append(os.path.dirname(os.path.realpath(__file__)))


def set_active_window_pos(left, top, width, height):
    ctypes.windll.user32.SetProcessDPIAware()

    hwnd = ctypes.windll.user32.GetForegroundWindow()

    arect = ctypes.wintypes.RECT()
    DWMWA_EXTENDED_FRAME_BOUNDS = 9
    ret = ctypes.windll.dwmapi.DwmGetWindowAttribute(
        ctypes.wintypes.HWND(hwnd),
        ctypes.wintypes.DWORD(DWMWA_EXTENDED_FRAME_BOUNDS),
        ctypes.byref(arect),
        ctypes.sizeof(arect),
    )
    if ret != 0:
        raise Exception("DwmGetWindowAttribute failed")

    rect = ctypes.wintypes.RECT()
    ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
    dx = rect.left - arect.left
    dy = rect.top - arect.top
    dw = rect.right - arect.right - dx
    dh = rect.bottom - arect.bottom - dy
    ctypes.windll.user32.MoveWindow(
        hwnd, left + dx, top + dy, width + dw, height + dh, True
    )


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
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        for line in self.captura_ps.stdout:
            line = line.decode(errors="ignore")
            if "Press p to pause or resume" in line:
                print("Recording started.")
                break

        time.sleep(0.2)

    def stop_record(self):
        if self.captura_ps is None:
            return

        self.captura_ps.stdin.write(b"q")
        self.captura_ps.stdin.close()
        self.captura_ps.wait()
        print("Recording stopped.")
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
            os.path.expandvars("%USERPROFILE%\\Videos\\**\\*.mp4"),
            recursive=True,
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


class FFmpegScreenRecorder(ScreenRecorder):
    def __init__(self):
        super().__init__()

        self.tmp_file = os.path.join(gettempdir(), "screen-record.mp4")
        self.proc = None
        self.loudnorm = False

    def start_record(self):
        logging.debug("FFmpegScreenRecorder.start_record()")

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
        time.sleep(0.2)

        print("Recording started.")

    def stop_record(self):
        logging.debug("FFmpegScreenRecorder.stop_record()")
        if self.proc is None:
            return

        self.proc.stdin.write(b"q")
        self.proc.stdin.close()
        self.proc.wait()
        print("Recording stopped.")
        self.proc = None

    def save(self, file):
        # Save file
        if os.path.exists(file):
            os.remove(file)

        move_file(self.tmp_file, file)


recorder = FFmpegScreenRecorder()

_cur_file = None


def start_record(file, rect=(0, 0, 1920, 1080)):
    global _cur_file

    _cur_file = file
    recorder.rect = rect
    recorder.start_record()


def stop_record():
    recorder.stop_record()
    recorder.save(_cur_file)


def record_screen(file, uia_callback=None, rect=(0, 0, 1920, 1080)):
    recorder.rect = rect

    if uia_callback is None:
        print2(f'Press F1 to screencap to "{file}"', color="green")
        wait_for_key("f1")

    recorder.start_record()

    if uia_callback is None:
        print2("Press F1 again to stop recording.", color="green")
        wait_for_key("f1")

    else:
        uia_callback()

    recorder.stop_record()
    recorder.save(file)


app = Application()


def start_application(args, title=None, restart=False, size=(1920, 1080)):
    if title:
        logging.debug("find window by title: %s", title)
        try:
            app.connect(title=title)
            if restart:
                app.kill(soft=True)
        except pywinauto.findwindows.ElementNotFoundError:
            restart = True

        if restart:
            start_process(["cmd", "/c", "start", ""] + args)
            app.connect(title=title, timeout=5)

        logging.debug("wait for window...")
        window = app.window(title=title)
        window.wait("exists")
    else:
        handle = old_handle = ctypes.windll.user32.GetForegroundWindow()
        start_process(["cmd", "/c", "start", ""] + args)
        while handle == old_handle:
            handle = ctypes.windll.user32.GetForegroundWindow()
            time.sleep(0.1)

        app.connect(handle=handle, timeout=5)
        window = app.window(handle=handle)

    logging.debug("move window")
    window.set_focus()
    set_active_window_pos(0, 0, size[0], size[1])
    # window.move_window(x=pos[0], y=pos[1], width=pos[2], height=pos[3])


def record_app(*, file, args, title=None, uia_callback=None, size=(1920, 1080)):
    start_application(args=args, title=title, size=size)
    record_screen(file, uia_callback=uia_callback, rect=[0, 0, size[0], size[1]])


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

    if args.out_dir:
        out_dir = args.out_dir
    else:
        out_dir = get_variable("SCREEN_RECORD_DIR")
        if not out_dir:
            out_dir = os.path.expanduser("~/Desktop")

    minimize_cur_terminal()

    while True:
        recorder.start_record()

        pressed = wait_for_key(["f6", "f7"])
        if pressed == "f6":
            print("Canceling record...")
            recorder.stop_record()
            continue

        elif pressed == "f7":
            print("Stoping record...")
            recorder.stop_record()
            break

    activate_cur_terminal()
    file = prompt_record_file_name()
    recorder.save(file)

    # Open file
    call_echo(["mpv", file])

    time.sleep(1)
