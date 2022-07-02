import atexit
import logging
import os
import subprocess
import time

from _script import wrap_args_alacritty
from _shutil import setup_logger, shell_open, write_temp_file

from .common import run_commands
from .record_screen import record_screen, start_application

root = os.path.dirname(os.path.abspath(__file__))


def open_alacritty(
    args=["wsl", "-e", "sh", "-c", "cd $HOME; bash"],
    restart=True,
    font_size=14,
    **kwargs,
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
        **kwargs,
    )
    start_application(args=args, title=title, restart=restart)
    time.sleep(0.2)


def open_cmd(cmd=None, **kwargs):
    tmp_batch_file = write_temp_file(
        (f"{cmd}&" if cmd else "") + r"set PROMPT=$e[0;37m$P$G$E[1;37m& echo.&cls",
        ".cmd",
    )
    args = [
        "cmd",
        "/k",
        f"call {tmp_batch_file}",
    ]
    open_alacritty(args=args, **kwargs)


def open_bash(**kwargs):
    args = ["wsl", "-e", "sh", "-c", "cd $HOME; bash"]
    open_alacritty(args=args, **kwargs)


def record_term(
    *,
    file,
    cmd=None,
    size=(1920, 1080),
    open_term_func=open_bash,
    dry_run=False,
    **kwargs,
):
    logging.info("record_term: %s", file)
    open_term_func(restart=False, **kwargs)

    if dry_run:
        if cmd is not None:
            run_commands(cmd, no_sleep=dry_run)

    else:
        record_screen(
            file,
            uia_callback=(lambda: (run_commands(cmd), time.sleep(0.2)))
            if cmd is not None
            else None,
            rect=(0, 0, size[0], size[1]),
        )

    return file


if __name__ == "__main__":
    setup_logger()
    file = os.path.expanduser("~/Desktop/test.mp4")
    # record_term(file=file, cmd=None)
    record_term(file=file, cmd="echo hello, world!\n")
    shell_open(file)
