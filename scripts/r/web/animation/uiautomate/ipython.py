import os

from _script import wt_wrap_args
from _shutil import *
from r.web.animation.record_screen import recorder
from uiautomate import *

root = os.path.dirname(os.path.abspath(__file__))


def open_wt_ipython(startup=None):
    run_ahk(os.path.join(root, "show_overlay.ahk"))
    time.sleep(2)

    startup_file = os.path.join(root, "_ipython_prompt.py")
    s = open(startup_file, "r").read()
    if startup is not None:
        s += "\n" + startup
    temp_file = write_temp_file(s, ".py")

    args = ["ipython", "-i", temp_file]

    args = wt_wrap_args(
        args,
        title="ross@ross-desktop2: IPython",
        font_size=14,
        icon=(root + "/python.ico").replace("\\", "/"),
        opacity=0.9,
    )
    call_echo(args)

    exec_ahk(
        """
        #include <Window>
        WinWaitActive, ahk_exe WindowsTerminal.exe
        SetWindowPos("A", 240, 125, 1440, 810)
        """
    )
    sleep(1)


if __name__ == "__main__":
    open_wt_ipython()
