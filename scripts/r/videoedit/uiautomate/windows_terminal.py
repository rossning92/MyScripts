import os
import time

from _script import wrap_args_wt
from _shutil import call_echo, exec_ahk, run_ahk

from .common import run_commands, send_hotkey
from .record_screen import start_record, stop_record

root = os.path.dirname(os.path.abspath(__file__))


def open_wt(args=["cmd"], size=(1440, 810), **kwargs):
    call_echo(["powershell", "-command", "Set-WinUserLanguageList -Force 'en-US'"])

    args = wrap_args_wt(args, **kwargs)
    call_echo(args)

    exec_ahk(
        """
        #include <Window>
        WinWaitActive, ahk_exe WindowsTerminal.exe
        SetWindowPos("A", -1, -1, %d, %d)
        """
        % (size[0] + 2, size[1] + 2)
    )
    time.sleep(1)


def close_wt():
    send_hotkey("alt", "f4")
    time.sleep(1)

    call_echo(
        ["powershell", "-command", "Set-WinUserLanguageList -Force 'en-US', 'zh-CN'"]
    )


def open_wt_with_bg():
    run_ahk(os.path.join(root, "show_overlay.ahk"))
    time.sleep(2)

    open_wt(
        icon=root + "/icons/cmd.png",
        title="Command Prompt",
        opacity=0.9,
    )
    time.sleep(2)

    exec_ahk(
        """
        #include <Window>
        WinWaitActive, ahk_exe WindowsTerminal.exe
        SetWindowPos("A", 128, 125, 1664, 810)
        """
    )
    time.sleep(0.5)


def record_windows_terminal(file, args, cmd, sound=False, size=(1440, 810), **kwargs):
    open_wt(args, size=size, **kwargs)

    start_record(file, (0, 0, size[0], size[1]))

    run_commands(cmd=cmd, sound=sound)

    stop_record()

    close_wt()
    return file
