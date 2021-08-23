import os

from _script import wt_wrap_args
from _shutil import *
from videoedit.record_screen import recorder

from .uiautomate import recorder, run_commands, send_hotkey

root = os.path.dirname(os.path.abspath(__file__))


def open_wt_ipython(startup=None, font_size=14):
    # run_ahk(os.path.join(root, "show_overlay.ahk"))
    # time.sleep(2)

    startup_file = os.path.join(root, "_ipython_prompt.py")
    s = open(startup_file, "r").read()
    if startup is not None:
        s += "\n" + startup
    temp_file = write_temp_file(s, ".py")

    args = ["ipython", "-i", temp_file]

    args = wt_wrap_args(
        args,
        title="ross@ross-desktop2: IPython",
        font_size=font_size,
        icon=(root + "/icons/python.ico").replace("\\", "/"),
    )
    call_echo(args)

    # SetWindowPos("A", 240, 125, 1440, 810)
    exec_ahk(
        """
        #include <Window>
        WinWaitActive, ahk_exe WindowsTerminal.exe
        SetWindowPos("A", -1, -1, 1442, 812)
        """
    )
    sleep(1)


def record_ipython(file, cmds, startup=None, font_size=14):
    call_echo(["powershell", "-command", "Set-WinUserLanguageList -Force 'en-US'"])

    open_wt_ipython(startup=startup, font_size=font_size)

    recorder.rect = (0, 0, 1440, 810)

    recorder.start_record()

    run_commands(cmds)

    time.sleep(2)
    recorder.stop_record()
    recorder.save_record(file)

    send_hotkey("alt", "f4")
    time.sleep(1)

    call_echo(
        ["powershell", "-command", "Set-WinUserLanguageList -Force 'zh-CN', 'en-US'"]
    )

    return file


if __name__ == "__main__":
    open_wt_ipython()
