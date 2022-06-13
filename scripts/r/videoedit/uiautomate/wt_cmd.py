import os
import time

from _shutil import shell_open

from .common import run_commands
from .record_screen import start_record, stop_record
from .windows_terminal import close_wt, open_wt

root = os.path.dirname(os.path.abspath(__file__))


def open_wt_cmd(startup=None, cwd=None, **kwargs):
    args = [
        "cmd",
        "/k",
        (f"{startup} && " if startup else "")
        + (f"cd {cwd} && " if cwd else "")
        + r"set PROMPT=$E[1;30m$P$G $E[1;37m&& echo.",
    ]

    open_wt(args, icon=root + "/icons/cmd.png", title="Command Prompt", **kwargs)


def record_wt_cmd(
    file, cmds, size=(1440, 810), **kwargs,
):
    open_wt_cmd(size=size, **kwargs)

    start_record(file, (0, 0, size[0], size[1]))

    run_commands(cmds)
    time.sleep(5)

    stop_record()

    close_wt()
    return file


if __name__ == "__main__":
    # open_wt_with_bg()
    # open_wt_cmd()

    file = os.path.expanduser("~/Desktop/test.mp4")
    record_wt_cmd(file, "echo 1{sleep 2}\n", cwd="C:\\")
    shell_open(file)
