import atexit
import ctypes
import logging
import os
import subprocess
import sys
import time

from _shutil import write_temp_file
from utils.logger import setup_logger
from utils.shutil import shell_open
from utils.term.alacritty import wrap_args_alacritty
from utils.window import set_window_rect

from .common import run_commands
from .record_screen import (
    DEFAULT_WINDOW_SIZE,
    record_screen,
    start_application,
)

root = os.path.dirname(os.path.abspath(__file__))


def _initialize_language_list():
    subprocess.call(
        ["powershell", "-command", "Set-WinUserLanguageList -Force 'en-US'"]
    )
    atexit.register(
        lambda: subprocess.call(
            [
                "powershell",
                "-command",
                "Set-WinUserLanguageList -Force 'en-US', 'zh-CN'",
            ]
        )
    )


def open_alacritty(
    args,
    restart=True,
    font_size=14,
    **kwargs,
):
    if sys.platform == "win32":
        _initialize_language_list()

    title = "AlacrittyAutomation"
    args = wrap_args_alacritty(
        args,
        title=title,
        font_size=font_size,
        borderless=True,
        padding=32,
        font="hack",
        **kwargs,
    )
    start_application(args=args, title=title, restart=restart)
    time.sleep(0.5)


def open_cmd(cmd=None, **kwargs):
    tmp_batch_file = write_temp_file(
        (f"{cmd}&" if cmd else "") + r"set PROMPT=$e[1;30m$P$G $e[0;37m&echo.&cls",
        ".cmd",
    )
    args = [
        "cmd",
        "/k",
        f"call {tmp_batch_file}",
    ]
    open_alacritty(args=args, **kwargs)


def open_bash(cwd="$HOME", **kwargs):
    args = ["wsl", "-e", "sh", "-c", "cd %s; bash" % cwd]
    open_alacritty(args=args, **kwargs)


def term(cmd):
    hwnd = 0
    while hwnd == 0:
        hwnd = ctypes.windll.user32.FindWindowW(None, "AlacrittyAutomation")
        time.sleep(0.1)
    set_window_rect(0, 0, DEFAULT_WINDOW_SIZE[0], DEFAULT_WINDOW_SIZE[1], hwnd=hwnd)
    run_commands(cmd, no_sleep=True)


def record_term(
    cmd,
    file,
    size=(1920, 1080),
    open_term_func=open_bash,
    **kwargs,
):
    logging.info("record_term: %s", file)
    open_term_func(restart=False, **kwargs)

    if file is None:
        if cmd is not None:
            run_commands(cmd, no_sleep=(file is None))

    else:
        record_screen(
            file,
            callback=(
                (lambda: (run_commands(cmd), time.sleep(0.2)))
                if cmd is not None
                else None
            ),
            rect=(0, 0, size[0], size[1]),
        )

    return file


if __name__ == "__main__":
    setup_logger()
    file = os.path.expanduser("~/Desktop/test.mp4")
    # record_term(file=file, cmd=None)
    record_term(file=file, cmd="echo hello, world!\n")
    shell_open(file)
