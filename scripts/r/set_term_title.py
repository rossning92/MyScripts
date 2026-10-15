import os
import sys


def _set_title_unix(title, tty):
    try:
        with open(tty, "w") as f:
            f.write(f"\033]0;{title}\007")
    except OSError:
        return False
    return True


def _set_title_windows(title):
    import ctypes
    from ctypes import wintypes

    WM_SETTEXT = 0x000C
    TH32CS_SNAPPROCESS = 0x00000002

    class PROCESSENTRY32(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", ctypes.c_char * 260),
        ]

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snapshot == -1:
        return False
    processes = {}
    pe = PROCESSENTRY32()
    pe.dwSize = ctypes.sizeof(PROCESSENTRY32)
    if kernel32.Process32First(snapshot, ctypes.byref(pe)):
        while True:
            processes[pe.th32ProcessID] = pe.th32ParentProcessID
            if not kernel32.Process32Next(snapshot, ctypes.byref(pe)):
                break
    kernel32.CloseHandle(snapshot)

    ancestor_depth = {}
    current = os.getpid()
    for depth in range(30):
        if current not in processes:
            break
        ancestor_depth[current] = depth
        current = processes[current]

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    found = []

    def enum_callback(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value in ancestor_depth:
            found.append((ancestor_depth[pid.value], hwnd))
        return True

    user32.EnumWindows(WNDENUMPROC(enum_callback), 0)
    if not found:
        return False
    found.sort()
    hwnd = found[0][1]
    ctypes.windll.user32.SendMessageW(hwnd, WM_SETTEXT, 0, title)
    return True


def set_term_title(title, tty=None):
    """Set the title of the terminal this process runs in, even when stdout is not that terminal."""
    if os.name == "nt":
        return _set_title_windows(title)
    return _set_title_unix(title, tty or "/dev/tty")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    title = " ".join(sys.argv[1:])
    if not set_term_title(title):
        sys.exit(1)
