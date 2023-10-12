import ctypes
import time


def _set_clip_win(text: str):
    from ctypes.wintypes import (
        BOOL,
        DWORD,
        HANDLE,
        HGLOBAL,
        HINSTANCE,
        HMENU,
        HWND,
        INT,
        LPCSTR,
        LPVOID,
        UINT,
    )

    u32 = ctypes.windll.user32
    k32 = ctypes.windll.kernel32

    CreateWindowExA = u32.CreateWindowExA
    CreateWindowExA.argtypes = [
        DWORD,
        LPCSTR,
        LPCSTR,
        DWORD,
        INT,
        INT,
        INT,
        INT,
        HWND,
        HMENU,
        HINSTANCE,
        LPVOID,
    ]
    CreateWindowExA.restype = HWND

    DestroyWindow = u32.DestroyWindow
    DestroyWindow.argtypes = [HWND]
    DestroyWindow.restype = BOOL

    OpenClipboard = u32.OpenClipboard
    OpenClipboard.argtypes = [HWND]
    OpenClipboard.restype = BOOL

    CloseClipboard = u32.CloseClipboard
    CloseClipboard.argtypes = []
    CloseClipboard.restype = BOOL

    EmptyClipboard = u32.EmptyClipboard
    EmptyClipboard.argtypes = []
    EmptyClipboard.restype = BOOL

    GlobalAlloc = k32.GlobalAlloc
    GlobalAlloc.argtypes = [UINT, ctypes.c_size_t]
    GlobalAlloc.restype = HGLOBAL

    msvcrt = ctypes.CDLL("msvcrt")
    wcslen = msvcrt.wcslen
    wcslen.argtypes = [ctypes.c_wchar_p]
    wcslen.restype = UINT

    GlobalLock = k32.GlobalLock
    GlobalLock.argtypes = [HGLOBAL]
    GlobalLock.restype = LPVOID

    GlobalUnlock = k32.GlobalUnlock
    GlobalUnlock.argtypes = [HGLOBAL]
    GlobalUnlock.restype = BOOL

    SetClipboardData = u32.SetClipboardData
    SetClipboardData.argtypes = [UINT, HANDLE]
    SetClipboardData.restype = HANDLE

    # This function is heavily based on
    # http://msdn.com/ms649016#_win32_Copying_Information_to_the_Clipboard

    hwnd = CreateWindowExA(0, b"STATIC", None, 0, 0, 0, 0, 0, None, None, None, None)
    try:
        if not hwnd:
            raise Exception("Error calling CreateWindowExA()")

        # http://msdn.com/ms649048
        # If an application calls OpenClipboard with hwnd set to NULL,
        # EmptyClipboard sets the clipboard owner to NULL;
        # this causes SetClipboardData to fail.
        # => We need a valid hwnd to copy something.

        # Open clipboard
        # We may not get the clipboard handle immediately because
        # some other application is accessing it (?)
        # We try for at least 500ms to get the clipboard.
        t = time.time() + 0.5
        success = False
        while time.time() < t:
            success = OpenClipboard(hwnd)
            if success:
                break
            time.sleep(0.01)
        if not success:
            raise Exception("Error calling OpenClipboard")

        try:
            if not EmptyClipboard():
                raise Exception("Error calling EmptyClipboard()")

            if text:
                # http://msdn.com/ms649051
                # If the hMem parameter identifies a memory object,
                # the object must have been allocated using the
                # function with the GMEM_MOVEABLE flag.
                count = wcslen(text) + 1
                GMEM_MOVEABLE = 0x0002
                handle = GlobalAlloc(
                    GMEM_MOVEABLE, count * ctypes.sizeof(ctypes.c_wchar)
                )
                if not handle:
                    raise Exception("Error calling GlobalAlloc()")

                locked_handle = GlobalLock(handle)
                if not locked_handle:
                    raise Exception("Error calling GlobalLock()")

                ctypes.memmove(
                    ctypes.c_wchar_p(locked_handle),
                    ctypes.c_wchar_p(text),
                    count * ctypes.sizeof(ctypes.c_wchar),
                )

                if not GlobalUnlock(handle) and ctypes.get_errno():
                    raise Exception("Error calling GlobalUnlock()")

                CF_UNICODETEXT = 13
                if not SetClipboardData(CF_UNICODETEXT, handle):
                    raise Exception("Error calling SetClipboardData()")

        finally:
            if not CloseClipboard():
                raise Exception("Error calling CloseClipboard()")

    finally:
        if not DestroyWindow(hwnd):
            raise Exception("Error calling DestroyWindow()")
