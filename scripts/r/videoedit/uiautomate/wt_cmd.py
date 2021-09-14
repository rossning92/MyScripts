import os

from .windows_terminal import open_wt, record_windows_terminal
from _shutil import shell_open

root = os.path.dirname(os.path.abspath(__file__))


args = {
    "args": ["cmd", "/k", "echo."],
    "icon": root + "/icons/cmd.png",
    "title": "Command Prompt",
    "cwd": os.path.expanduser("~"),
    # "font_size": 14,
}


def record_wt_cmd(file, cmds, font_size=14):
    return record_windows_terminal(file, cmds=cmds, font_size=font_size, **args)


if __name__ == "__main__":
    # open_wt_with_bg()
    # open_wt_cmd()

    file = os.path.expanduser("~/Desktop/test.mp4")
    record_wt_cmd(file, "echo 1{sleep 2}\n")
    shell_open(file)
