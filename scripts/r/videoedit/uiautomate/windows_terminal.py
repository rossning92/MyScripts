import os
import time

from _script import wrap_args_wt
from _shutil import call_echo, exec_ahk, run_ahk

from .uiautomate import recorder, run_commands, send_hotkey

root = os.path.dirname(os.path.abspath(__file__))


def open_wt(args=["cmd"], **kwargs):
    args = wrap_args_wt(args, **kwargs)
    call_echo(args)


def open_wt_with_bg():
    run_ahk(os.path.join(root, "show_overlay.ahk"))
    time.sleep(2)

    open_wt(
        icon=root + "/icons/cmd.png", title="Command Prompt", opacity=0.9,
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


def record_windows_terminal(file, args, cmds, sound=False, size=(1440, 810), **kwargs):
    call_echo(["powershell", "-command", "Set-WinUserLanguageList -Force 'en-US'"])

    open_wt(args, **kwargs)

    exec_ahk(
        """
        #include <Window>
        WinWaitActive, ahk_exe WindowsTerminal.exe
        SetWindowPos("A", -1, -1, %d, %d)
        """
        % (size[0] + 2, size[1] + 2)
    )
    time.sleep(1)

    recorder.rect = (0, 0, size[0], size[1])

    recorder.start_record()

    run_commands(cmds, sound=sound)

    time.sleep(2)
    recorder.stop_record()
    recorder.save_record(file)

    send_hotkey("alt", "f4")
    time.sleep(1)

    call_echo(
        ["powershell", "-command", "Set-WinUserLanguageList -Force 'en-US', 'zh-CN'"]
    )

    return file
