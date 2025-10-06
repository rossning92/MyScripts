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
from typing import Optional

import pyautogui
from _script import get_variable, set_variable
from _shutil import (
    call_echo,
    get_next_file_name,
    get_temp_file_name,
    move_file,
    print2,
    start_process,
    wait_for_key,
)
from _video import ffmpeg
from audio.postprocess import loudnorm
from pynput import keyboard
from utils.slugify import slugify
from utils.window import get_window_rect

sys.path.append(os.path.dirname(os.path.realpath(__file__)))


DEFAULT_WINDOW_SIZE = (1920, 1080)


def _get_default_monitor_source() -> Optional[str]:
    try:
        # Get default output device
        source = subprocess.check_output(
            ["pactl", "get-default-sink"],
            text=True,
        ).strip()
        return source + ".monitor"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def set_window_pos(left, top, width, height, hwnd=None):
    if hwnd is None:
        hwnd = ctypes.windll.user32.GetForegroundWindow()

    logging.debug("set window pos")
    ctypes.windll.user32.SetProcessDPIAware()
    ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    ctypes.windll.user32.SetForegroundWindow(hwnd)

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

    time.sleep(0.1)


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

    def is_recording(self) -> bool:
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
        ]

        if sys.platform.startswith("win"):
            args += [
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
                    f"{self.rect[2] // 2 * 2}x{self.rect[3] // 2 * 2}",
                ]

            args += [
                "-draw_mouse",
                "1",
                "-i",
                "desktop",
            ]
        else:
            if self.rect is not None:
                x, y, width, height = self.rect
            else:
                screen_width, screen_height = pyautogui.size()
                x, y = 0, 0
                width, height = screen_width, screen_height

            display = os.environ.get("DISPLAY", ":0.0")
            args += [
                "-f",
                "x11grab",
                "-framerate",
                "60",
                "-video_size",
                f"{width // 2 * 2}x{height // 2 * 2}",
                "-i",
                f"{display}+{x},{y}",
            ]

            if not self.no_audio:
                source = _get_default_monitor_source()
                if not source:
                    raise Exception("Failed to find any audio monitor source")
                args += ["-f", "pulse", "-i", source]

        args += [
            "-c:v",
            "libx264",
            "-r",
            "60",
            "-preset",
            "ultrafast",
            "-crf",
            "19",
            "-pix_fmt",
            "yuv420p",
        ]

        if not self.no_audio:
            args += [
                "-c:a",
                "aac",
                "-b:a",
                "160k",
            ]
        else:
            args += ["-an"]

        args += [
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

    def is_recording(self) -> bool:
        return self.proc is not None


recorder = FFmpegScreenRecorder()

_cur_file = None


def start_record(file, rect=(0, 0, DEFAULT_WINDOW_SIZE[0], DEFAULT_WINDOW_SIZE[1])):
    global _cur_file

    _cur_file = file
    recorder.rect = rect
    recorder.start_record()


def stop_record():
    recorder.stop_record()
    recorder.save(_cur_file)


def record_screen(
    file, callback=None, rect=(0, 0, DEFAULT_WINDOW_SIZE[0], DEFAULT_WINDOW_SIZE[1])
):
    recorder.rect = rect

    if callback is None:
        print2(f'Press F1 to screencap to "{file}"', color="green")
        wait_for_key("f1")

    recorder.start_record()

    if callback is None:
        print2("Press F1 again to stop recording.", color="green")
        wait_for_key("f1")

    else:
        callback()

    recorder.stop_record()
    recorder.save(file)


def start_application(args, title=None, restart=False, size=DEFAULT_WINDOW_SIZE):
    if title:
        logging.debug("find window by title: %s", title)
        hwnd = ctypes.windll.user32.FindWindowW(None, title)
        if restart or hwnd == 0:
            if hwnd:
                logging.debug("close window: %s", title)
                WM_CLOSE = 0x10
                ctypes.windll.user32.PostMessageA(hwnd, WM_CLOSE, 0, 0)
                time.sleep(0.5)
                hwnd = 0

            logging.debug("run %s" % args)
            start_process(["cmd", "/c", "start", ""] + args)

        while not hwnd:
            hwnd = ctypes.windll.user32.FindWindowW(None, title)
            time.sleep(0.1)
    else:
        hwnd = old_hwnd = ctypes.windll.user32.GetForegroundWindow()
        start_process(["cmd", "/c", "start", ""] + args)
        while hwnd == old_hwnd:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            time.sleep(0.1)

    set_window_pos(0, 0, size[0], size[1], hwnd=hwnd)


def record_app(*, file, args=None, title=None, callback=None, size=DEFAULT_WINDOW_SIZE):
    if args is not None:
        start_application(args=args, title=title, size=size)
    record_screen(file, callback=callback, rect=[0, 0, size[0], size[1]])


def prompt_record_file_name():
    args = ["zenity", "--entry", "--text=Enter file name:"]

    last_file_name = get_variable("LAST_SCREEN_RECORD_FILE_NAME")
    if last_file_name:
        suggest_file_name = get_next_file_name(last_file_name)
        args.append(f"--entry-text={suggest_file_name}")

    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
    )
    name = result.stdout.strip()
    if not name:
        return None

    set_variable("LAST_SCREEN_RECORD_FILE_NAME", name)
    file = os.path.join(out_dir, "%s.mp4" % slugify(name))
    return file


def on_press(key):
    if key == keyboard.Key.f9:
        if not recorder.is_recording():
            recorder.rect = get_window_rect()
            recorder.start_record()
        else:
            recorder.stop_record()
            file = prompt_record_file_name()
            if file:
                recorder.save(file)
                call_echo(["mpv", file])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--rect",
        type=int,
        nargs="+",
        default=(0, 0, DEFAULT_WINDOW_SIZE[0], DEFAULT_WINDOW_SIZE[1]),
    )
    parser.add_argument("--no_audio", default=False, action="store_true")
    parser.add_argument("--out_dir", type=str, default=None)
    parser.add_argument("--window-name", type=str, default=None)

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

    if args.window_name:
        recorder.rect = get_window_rect(args.window_name)
        recorder.start_record()

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()
