import os

from _script import wt_wrap_args
from _shutil import *
from r.web.animation.record_screen import recorder
from uiautomate import *

root = os.path.dirname(os.path.abspath(__file__))


def open_windows_terminal():
    args = ["cmd"]

    args = wt_wrap_args(
        args,
        title="Command Prompt",
        font_size=14,
        icon=(root + "/cmd.png").replace("\\", "/"),
        opacity=0.9,
    )
    call_echo(args, cwd=os.path.expanduser("~"))


if __name__ == "__main__":
    run_ahk(os.path.join(root, "show_overlay.ahk"))
    time.sleep(2)

    open_windows_terminal()
    time.sleep(2)

    exec_ahk(
        """
        #include <Window>
        WinWaitActive, ahk_exe WindowsTerminal.exe
        SetWindowPos("A", 128, 125, 1664, 810)
        """
    )
    sleep(0.5)
