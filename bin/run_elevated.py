import ctypes
import logging
import subprocess
import sys
from typing import List, Union


def run_elevated(args: Union[List[str], str], wait=True, show_terminal_window=True):
    if sys.platform == "win32":
        import win32con
        from win32com.shell import shellcon
        from win32com.shell.shell import ShellExecuteEx

        if isinstance(args, str):
            lpFile, lpParameters = args.split(" ", 1)
        else:
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
    else:
        if isinstance(args, str):
            args = "sudo " + args
        else:
            args = ["sudo"] + args
        logging.info("run_elevated(): %s" % args)
        ret = subprocess.call(args, shell=True)
    return ret


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_elevated(sys.argv[1:])
    else:
        print("No arguments provided to run elevated.")
