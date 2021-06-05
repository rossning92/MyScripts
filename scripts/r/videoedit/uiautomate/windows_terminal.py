import os

from _script import wt_wrap_args
from _shutil import run_ahk, call_echo
from videoedit.record_screen import recorder
from uiautomate import run_ahk, exec_ahk
import time

root = os.path.dirname(os.path.abspath(__file__))


def open_wt(args=["cmd"], icon=root + "/icons/cmd.png", title="Command Prompt"):
    args = wt_wrap_args(
        args, title=title, font_size=14, icon=icon.replace("\\", "/"), opacity=0.9,
    )
    call_echo(args, cwd=os.path.expanduser("~"))


def open_wt_with_bg():
    run_ahk(os.path.join(root, "show_overlay.ahk"))
    time.sleep(2)

    open_wt()
    time.sleep(2)

    exec_ahk(
        """
        #include <Window>
        WinWaitActive, ahk_exe WindowsTerminal.exe
        SetWindowPos("A", 128, 125, 1664, 810)
        """
    )
    time.sleep(0.5)


def open_wt_bash():
    open_wt(args=["bash"], icon=root+"/icons/linux.ico", title="ross@ross-desktop2")


if __name__ == "__main__":
    # open_wt_with_bg()
    open_wt_bash()
