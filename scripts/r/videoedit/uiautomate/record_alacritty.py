import atexit
import logging
import os
import subprocess
import time

from _script import wrap_args_alacritty
from _shutil import setup_logger, shell_open

from .common import run_commands
from .record_screen import record_screen, start_application

root = os.path.dirname(os.path.abspath(__file__))


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
    args = wrap_args_alacritty(
        args,
        title=title,
        font_size=font_size,
        borderless=True,
        padding=32,
        font="hack",
        **kwargs
    )
    start_application(args=args, title=title, restart=restart)


def record_alacritty(*, file, cmds=None, size=(1920, 1080), **kwargs):
    logging.info("record_alacritty: %s", file)
    open_alacritty(restart=False, **kwargs)
    time.sleep(0.2)

    record_screen(
        file,
        uia_callback=(lambda: (run_commands(cmds), time.sleep(0.2)))
        if cmds is not None
        else None,
        rect=(0, 0, size[0], size[1]),
    )

    return file


if __name__ == "__main__":
    setup_logger()
    file = os.path.expanduser("~/Desktop/test.mp4")
    # record_alacritty(file=file, cmds=None)
    record_alacritty(file=file, cmds="echo hello, world!\n")
    shell_open(file)
