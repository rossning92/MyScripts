import argparse
import ctypes
import logging
import os
import subprocess
import sys
import time
from tempfile import gettempdir
from typing import Optional

from _script import get_variable, set_variable
from _shutil import (
    call_echo,
    get_next_file_name,
    move_file,
    print2,
    start_process,
    wait_for_key,
)
from pynput import keyboard
from utils.notify import send_notify
from utils.slugify import slugify
from utils.window import get_window_rect, set_window_rect

sys.path.append(os.path.dirname(os.path.realpath(__file__)))


DEFAULT_WINDOW_SIZE = (1920, 1080)


def to_float(name: str) -> Optional[float]:
    value = os.getenv(name)
    return float(value) if value else None


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


class ScreenRecorder:
    def __init__(self, no_audio, rect):
        super().__init__()
        self.no_audio = no_audio
        self.rect = rect
        self.tmp_file = os.path.join(gettempdir(), "screen-record.mp4")
        self.proc = None
        self.loudnorm = False

    def start_record(self):
        logging.debug("start_record()")

        if self.proc is not None:
            return

        args = [
            "ffmpeg",
            "-hide_banner",
        ]

        if self.rect:
            rect = self.rect
        else:
            rect = get_window_rect()

        if sys.platform.startswith("win"):
            args += [
                "-f",
                "gdigrab",
                "-framerate",
                "60",
            ]

            args += [
                "-offset_x",
                f"{rect[0]}",
                "-offset_y",
                f"{rect[1]}",
                "-video_size",
                f"{rect[2] // 2 * 2}x{rect[3] // 2 * 2}",
            ]

            args += [
                "-draw_mouse",
                "1",
                "-i",
                "desktop",
            ]
        else:
            x, y, width, height = rect

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

        self.proc = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            bufsize=1,
        )

        start_time = time.time()
        while True:
            if self.proc.poll() is not None:
                raise RuntimeError("ffmpeg exited before recording started")

            line = self.proc.stderr.readline()
            if b"Press [q]" in line or b"frame=" in line:
                break

            if not line and time.time() - start_time > 5:
                raise TimeoutError("Timed out waiting for recording to start")

        send_notify("<span foreground='#00ff00'>Recording started</span>")

    def stop_record(self):
        logging.debug("stop_record()")
        if self.proc is None:
            return

        self.proc.stdin.write(b"q")
        self.proc.stdin.flush()
        self.proc.stdin.close()
        if self.proc.stderr:
            self.proc.stderr.close()
        self.proc.wait()
        send_notify("<span foreground='#00ff00'>Recording stopped</span>")
        self.proc = None

    def save(self, file):
        # Save file
        if os.path.exists(file):
            os.remove(file)

        move_file(self.tmp_file, file)

    def is_recording(self) -> bool:
        return self.proc is not None


_recorder = None
_cur_file = None


def start_record(file, rect=None, window_name=None):
    global _cur_file, _recorder

    _cur_file = file
    rect = None
    print(f'Querying window rect for "{window_name}"', end="")
    while not rect:
        rect = get_window_rect(window_name=window_name)
        time.sleep(0.1)
    _recorder = ScreenRecorder()
    _recorder.rect = rect
    _recorder.start_record()


def stop_record():
    _recorder.stop_record()
    _recorder.save(_cur_file)


def record_screen(file, callback=None, rect=None):
    _recorder.rect = rect

    if callback is None:
        print2(f'Press F1 to screencap to "{file}"', color="green")
        wait_for_key("f1")

    _recorder.start_record()

    if callback is None:
        print2("Press F1 again to stop recording.", color="green")
        wait_for_key("f1")

    else:
        callback()

    _recorder.stop_record()
    _recorder.save(file)


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

    set_window_rect(0, 0, size[0], size[1], hwnd=hwnd)


def record_app(*, file, args=None, title=None, callback=None, size=DEFAULT_WINDOW_SIZE):
    if args is not None:
        start_application(args=args, title=title, size=size)
    record_screen(file, callback=callback, rect=[0, 0, size[0], size[1]])


def _prompt_record_file_name():
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
    return "%s.mp4" % slugify(name)


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rect", type=int, nargs="+")
    parser.add_argument("--no_audio", default=True, action="store_true")
    parser.add_argument("--out_dir", type=str, default=None)
    parser.add_argument("--window-name", type=str, default=None)
    parser.add_argument(
        "--max-length",
        type=float,
        default=to_float("MAX_LENGTH"),
        help="Max record length in seconds",
    )

    args = parser.parse_args()

    if args.window_name:
        rect = get_window_rect(args.window_name)
    else:
        rect = args.rect

    recorder = ScreenRecorder(no_audio=args.no_audio, rect=rect)

    if args.out_dir:
        out_dir = args.out_dir
    else:
        out_dir = get_variable("SCREEN_RECORD_DIR")
        if not out_dir:
            out_dir = os.path.expanduser("~/Desktop")
    os.chdir(out_dir)

    def on_press(key):
        if key == keyboard.Key.f8:
            if not recorder.is_recording():
                recorder.start_record()
                if args.max_length:
                    time.sleep(args.max_length)
                    should_stop = True
                else:
                    should_stop = False
            else:
                should_stop = True

            if should_stop:
                recorder.stop_record()
                file = _prompt_record_file_name()
                if file:
                    recorder.save(file)
                    call_echo(["mpv", file])

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()


if __name__ == "__main__":
    _main()
