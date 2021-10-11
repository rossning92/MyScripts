import os

from _shutil import shell_open, write_temp_file

from .windows_terminal import record_windows_terminal

root = os.path.dirname(os.path.abspath(__file__))


def record_ipython(file, cmds, startup=None, font_size=14):
    startup_file = os.path.join(root, "_ipython_prompt.py")
    s = open(startup_file, "r").read()
    if startup is not None:
        s += "\n" + startup
    temp_file = write_temp_file(s, ".py")

    args = ["ipython", "-i", temp_file]

    return record_windows_terminal(
        file,
        args=args,
        cmds=cmds,
        title="ross@ross-desktop2: IPython",
        font_size=font_size,
        icon=(root + "/icons/python.ico").replace("\\", "/"),
    )


if __name__ == "__main__":
    file = os.path.expanduser("~/Desktop/test.mp4")
    record_ipython(file, "1 + 1{sleep 1}\n2 + 2")
    shell_open(file)
