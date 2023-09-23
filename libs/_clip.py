import ctypes
import ctypes.wintypes
import shutil
import subprocess
import sys
import time
from functools import lru_cache


def _get_clip_win():
    if sys.platform != "win32":
        raise Exception("The function can only be called on Windows.")

    CF_UNICODETEXT = 13

    u32 = ctypes.windll.user32
    k32 = ctypes.windll.kernel32

    OpenClipboard = u32.OpenClipboard
    OpenClipboard.argtypes = (ctypes.wintypes.HWND,)
    OpenClipboard.restype = ctypes.wintypes.BOOL

    GetClipboardData = u32.GetClipboardData
    GetClipboardData.argtypes = (ctypes.wintypes.UINT,)
    GetClipboardData.restype = ctypes.wintypes.HANDLE

    GlobalLock = k32.GlobalLock
    GlobalLock.argtypes = (ctypes.wintypes.HGLOBAL,)
    GlobalLock.restype = ctypes.wintypes.LPVOID

    GlobalUnlock = k32.GlobalUnlock
    GlobalUnlock.argtypes = (ctypes.wintypes.HGLOBAL,)
    GlobalUnlock.restype = ctypes.wintypes.BOOL

    CloseClipboard = u32.CloseClipboard
    CloseClipboard.argtypes = ()
    CloseClipboard.restype = ctypes.wintypes.BOOL

    text = ""
    if OpenClipboard(None):
        h_clip_mem = GetClipboardData(CF_UNICODETEXT)
        text = ctypes.wstring_at(GlobalLock(h_clip_mem))
        GlobalUnlock(h_clip_mem)
        CloseClipboard()
    return text


def get_clip():
    if _is_termux():
        return subprocess.check_output(
            ["termux-clipboard-get"], universal_newlines=True
        )

    elif sys.platform == "win32":
        return _get_clip_win()

    elif sys.platform == "linux":
        return subprocess.check_output(
            ["xclip", "-out", "-selection", "clipboard"], universal_newlines=True
        )


def _get_selection_win():
    if sys.platform != "win32":
        raise Exception("The function can only be called on Windows.")

    LONG = ctypes.c_long
    DWORD = ctypes.c_ulong
    ULONG_PTR = ctypes.POINTER(DWORD)
    WORD = ctypes.c_ushort

    INPUT_KEYBOARD = 1
    VK_CONTROL = 0x11
    KEYEVENTF_KEYUP = 0x0002
    KEY_C = 0x43

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = (
            ("dx", LONG),
            ("dy", LONG),
            ("mouseData", DWORD),
            ("dwFlags", DWORD),
            ("time", DWORD),
            ("dwExtraInfo", ULONG_PTR),
        )

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = (
            ("wVk", WORD),
            ("wScan", WORD),
            ("dwFlags", DWORD),
            ("time", DWORD),
            ("dwExtraInfo", ULONG_PTR),
        )

    class HARDWAREINPUT(ctypes.Structure):
        _fields_ = (("uMsg", DWORD), ("wParamL", WORD), ("wParamH", WORD))

    class _INPUTunion(ctypes.Union):
        _fields_ = (("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT))

    class INPUT(ctypes.Structure):
        _fields_ = (("type", DWORD), ("union", _INPUTunion))

    def SendInput(*inputs):
        nInputs = len(inputs)
        LPINPUT = INPUT * nInputs
        pInputs = LPINPUT(*inputs)
        cbSize = ctypes.c_int(ctypes.sizeof(INPUT))
        return ctypes.windll.user32.SendInput(nInputs, pInputs, cbSize)

    def KeybdInput(code, flags=0):
        return INPUT(
            INPUT_KEYBOARD, _INPUTunion(ki=KEYBDINPUT(code, code, flags, 0, None))
        )

    def send_ctrl_c():
        SendInput(KeybdInput(VK_CONTROL), KeybdInput(KEY_C))
        time.sleep(0.1)
        SendInput(
            KeybdInput(VK_CONTROL, KEYEVENTF_KEYUP), KeybdInput(KEY_C, KEYEVENTF_KEYUP)
        )
        time.sleep(0.1)

    send_ctrl_c()

    return _get_clip_win()


@lru_cache(maxsize=None)
def _is_termux():
    return shutil.which("termux-setup-storage") is not None


def get_selection():
    if _is_termux():
        return subprocess.check_output(
            ["termux-clipboard-get"], universal_newlines=True
        )

    elif sys.platform == "linux":
        return subprocess.check_output(
            ["xclip", "-out", "-selection", "primary"], universal_newlines=True
        )

    elif sys.platform == "win32":
        return _get_selection_win()

    else:
        raise Exception(f"Unsupported OS: {sys.platform}")
