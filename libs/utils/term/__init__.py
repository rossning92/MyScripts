import ctypes
import locale
import os
import subprocess
import sys
from typing import Dict, List, Optional

from _shutil import quote_arg, write_temp_file


def activate_cur_terminal():
    if sys.platform == "win32":
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        ctypes.windll.user32.SetForegroundWindow(hwnd)


def minimize_cur_terminal():
    if sys.platform == "win32":
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        ctypes.windll.user32.ShowWindow(hwnd, 6)


def clear_terminal():
    if sys.platform == "win32":
        subprocess.run(["cls"], check=False, shell=True)
        return

    if os.environ.get("TERM"):
        subprocess.run(["clear"], check=False)
        return

    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def get_terminal_title():
    if sys.platform == "win32":
        MAX_BUFFER = 260
        title_buff = (ctypes.c_char * MAX_BUFFER)()
        ret = ctypes.windll.kernel32.GetConsoleTitleA(title_buff, MAX_BUFFER)
        assert ret > 0
        return title_buff.value.decode(locale.getpreferredencoding())


def set_terminal_title(title):
    if sys.platform == "win32":
        win_title = title.encode(locale.getpreferredencoding())
        ctypes.windll.kernel32.SetConsoleTitleA(win_title)


def enable_windows_vt():
    """Enable Windows virtual terminal processing for console input and output."""
    assert sys.platform == "win32"

    from ctypes import wintypes

    # Windows API constants
    STD_INPUT_HANDLE = -10
    STD_OUTPUT_HANDLE = -11
    ENABLE_VIRTUAL_TERMINAL_INPUT = 0x0200
    ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
    ENABLE_EXTENDED_FLAGS = 0x0080

    kernel32 = ctypes.windll.kernel32

    # Enable VT input
    h_input = kernel32.GetStdHandle(STD_INPUT_HANDLE)
    in_mode = wintypes.DWORD()
    if kernel32.GetConsoleMode(h_input, ctypes.byref(in_mode)):
        new_in_mode = (
            in_mode.value | ENABLE_VIRTUAL_TERMINAL_INPUT | ENABLE_EXTENDED_FLAGS
        )
        kernel32.SetConsoleMode(h_input, new_in_mode)

    # Enable VT output
    h_output = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    out_mode = wintypes.DWORD()
    if kernel32.GetConsoleMode(h_output, ctypes.byref(out_mode)):
        new_out_mode = out_mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING
        kernel32.SetConsoleMode(h_output, new_out_mode)


def args_to_str(args, shell_type):
    assert type(args) in [list, tuple]
    return " ".join([quote_arg(x, shell_type=shell_type) for x in args])


def wrap_args_tee(args: List[str], out_file: str):
    assert isinstance(args, list)

    if sys.platform == "win32":
        s = (
            "$PSDefaultParameterValues = @{'Out-File:Encoding' = 'utf8'}; & "
            + args_to_str(args, shell_type="powershell")
            + r" | Tee-Object -FilePath %s" % out_file
        )
        tmp_file = write_temp_file(s, ".ps1")
        return ["powershell", tmp_file]
    else:
        return args


def wrap_args_cmd(
    args: List[str],
    title: Optional[str] = None,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
) -> str:
    if sys.platform == "win32":
        cmdline = "cmd /c "
        if title:
            cmdline += "title %s&" % quote_arg(title)
        if cwd:
            cmdline += "cd /d %s&" % quote_arg(cwd)
        if env:
            for k, v in env.items():
                cmdline += "&".join(['set "%s=%s"' % (k, v)]) + "&"
        cmdline += args_to_str(args, shell_type="cmd")
    else:
        cmdline = ""
        if env:
            for k, v in env.items():
                if k != "PATH":
                    cmdline += "%s=%s" % (k, v) + " "
        cmdline += args_to_str(args, shell_type="bash")

    return cmdline
