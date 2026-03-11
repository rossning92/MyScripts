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
