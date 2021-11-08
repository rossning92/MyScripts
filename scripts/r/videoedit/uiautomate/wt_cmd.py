import os

from .windows_terminal import open_wt, record_windows_terminal
from _shutil import shell_open

root = os.path.dirname(os.path.abspath(__file__))


def record_wt_cmd(
    file,
    cmds,
    font_size=14,
    icon=root + "/icons/cmd.png",
    title="Command Prompt",
    cwd=None,
    startup=None,
    **kwargs,
):
    args = [
        "cmd",
        "/k",
        (f"{startup} && " if startup else "")
        + (f"cd {cwd} && " if cwd else "")
        + r"set PROMPT=$E[1;30m$P$G $E[1;37m&& echo.",
    ]

    return record_windows_terminal(
        file,
        cmds=cmds,
        font_size=font_size,
        args=args,
        icon=icon,
        title=title,
        **kwargs,
    )


if __name__ == "__main__":
    # open_wt_with_bg()
    # open_wt_cmd()

    file = os.path.expanduser("~/Desktop/test.mp4")
    record_wt_cmd(file, "echo 1{sleep 2}\n", cwd="C:\\")
    shell_open(file)
