import ctypes
import subprocess
import sys
from typing import List


def run_elevated(args: List[str], wait=True, show_terminal_window=True):
    assert sys.platform == "win32"

    import win32con
    from win32com.shell import shellcon
    from win32com.shell.shell import ShellExecuteEx

    lpFile = args[0]
    lpParameters = subprocess.list2cmdline(args[1:])

    process_info = ShellExecuteEx(
        nShow=win32con.SW_SHOW if show_terminal_window else win32con.SW_HIDE,
        fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
        lpVerb="runas",
        lpFile=lpFile,
        lpParameters=lpParameters,
    )
    if wait:
        h = process_info["hProcess"].handle
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        if kernel32.WaitForSingleObject(h, 600000) == 0:  # WAIT_OBJECT_0
            exit_code = ctypes.c_ulong()
            if kernel32.GetExitCodeProcess(h, ctypes.byref(exit_code)):
                ret = exit_code.value
            else:
                raise ctypes.WinError(ctypes.get_last_error())
        else:
            raise Exception("WaitForSingleObject failed")

        kernel32.CloseHandle(h)
    else:
        ret = process_info
    return ret
