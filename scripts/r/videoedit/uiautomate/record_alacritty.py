import logging
import os
import time

from _script import wrap_args_alacritty
from _shutil import print2, setup_logger, shell_open, start_process, wait_for_key
from pywinauto.application import Application

from .common import run_commands
from .record_screen import start_record, stop_record, wait_for_key

root = os.path.dirname(os.path.abspath(__file__))

app = Application()


def open_alacritty(args, **kwargs):
    title = "AlacrittyAutomation"

    logging.debug("find window by title: %s", title)
    app.connect(title=title)
    window = app.window(title=title)
    if not window.exists():
        args = wrap_args_alacritty(
            args,
            title=title,
            font_size=14,
            borderless=True,
            padding=32,
            font="hack",
            **kwargs
        )
        start_process(args)

    logging.debug("wait for window...")
    window.wait("exists")

    logging.debug("move window")
    window.set_focus()
    window.move_window(x=0, y=0, width=1920, height=1080)


# def close_alacritty():
#     send_hotkey("alt", "f4")
#     time.sleep(1)

#     call_echo(
#         ["powershell", "-command", "Set-WinUserLanguageList -Force 'en-US', 'zh-CN'"]
#     )


def record_alacritty(*, file, cmds=None, size=(1920, 1080), **kwargs):
    logging.info("record_alacritty: %s", file)
    open_alacritty(args=["wsl", "-e", "sh", "-c", "cd $HOME; bash"], **kwargs)
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
