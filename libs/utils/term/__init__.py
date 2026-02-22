import ctypes
import locale
import os
import subprocess
import sys


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
