import atexit
import logging
import os
import subprocess
import time

import pywinauto
from _script import wrap_args_alacritty
from _shutil import print2, setup_logger, shell_open, start_process, wait_for_key
from pywinauto.application import Application

from .common import run_commands
from .record_screen import start_record, stop_record, wait_for_key

root = os.path.dirname(os.path.abspath(__file__))

app = Application()


def open_alacritty(
    args=["wsl", "-e", "sh", "-c", "cd $HOME; bash"],
    restart=True,
    font_size=14,
    **kwargs
):
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

    title = "AlacrittyAutomation"

    logging.debug("find window by title: %s", title)
    try:
        app.connect(title=title)
        if restart:
            app.kill(soft=True)
    except pywinauto.findwindows.ElementNotFoundError:
        restart = True

    if restart:
        args = wrap_args_alacritty(
            args,
            title=title,
            font_size=font_size,
            borderless=True,
            padding=32,
            font="hack",
            **kwargs
        )
        start_process(["cmd", "/c", "start"] + args)
        app.connect(title=title, timeout=5)

    logging.debug("wait for window...")
    window = app.window(title=title)
    window.wait("exists")

    logging.debug("move window")
    window.set_focus()
    window.move_window(x=0, y=0, width=1920, height=1080)


def record_alacritty(*, file, cmds=None, size=(1920, 1080), **kwargs):
    logging.info("record_alacritty: %s", file)
    open_alacritty(restart=False, **kwargs)
    time.sleep(0.2)

    if cmds is None:
        print2('Press F1 to screencap to "%s"' % file)
        wait_for_key("f1")

    start_record(file, (0, 0, size[0], size[1]))
    time.sleep(0.2)

    if cmds is not None:
        run_commands(cmds)
        time.sleep(0.2)

    if cmds is None:
        print2("Press F1 again to stop recording.")
        wait_for_key("f1")

    stop_record()

    # close_alacritty()
    return file


if __name__ == "__main__":
    setup_logger()
    file = os.path.expanduser("~/Desktop/test.mp4")
    record_alacritty(file=file, cmds=None)
    # record_alacritty(file=file, cmds="echo hello, world!\n")
    shell_open(file)
