import os

from .windows_terminal import open_wt, record_windows_terminal
from _shutil import shell_open

root = os.path.dirname(os.path.abspath(__file__))


args = {
    "args": ["bash", "-c", "cd ${HOME} && bash"],
    "icon": root + "/icons/linux.ico",
    "title": "ross@ross-desktop2",
    "cwd": os.path.expanduser("~"),
    "font_size": 14,
}


def record_wt_bash(file, cmds):
    return record_windows_terminal(file, cmds=cmds, **args,)


if __name__ == "__main__":
    file = os.path.expanduser("~/Desktop/test.mp4")
    record_wt_bash(file, "echo 1")
    shell_open(file)
