import ctypes
import logging
import os
import re
import shutil
import subprocess
import sys
from typing import Literal

TITLE_MATCH_MODE_EXACT = 0
TITLE_MATCH_MODE_PARTIAL = 1
TITLE_MATCH_MODE_START_WITH = 2
TITLE_MATCH_MODE_REGEX = 3
TITLE_MATCH_MODE_DEFAULT = TITLE_MATCH_MODE_REGEX


def _activate_window_win(hwnd):
    # Define the WINDOWPLACEMENT structure
    class WINDOWPLACEMENT(ctypes.Structure):
        _fields_ = [
            ("length", ctypes.c_uint),
            ("flags", ctypes.c_uint),
            ("showCmd", ctypes.c_uint),
            ("ptMinPosition", ctypes.c_long * 2),
            ("ptMaxPosition", ctypes.c_long * 2),
            ("rcNormalPosition", ctypes.c_long * 4),
            ("rcDevice", ctypes.c_long * 4),
        ]

    user32 = ctypes.windll.user32
    GetWindowPlacement = user32.GetWindowPlacement
    ShowWindow = user32.ShowWindow
    SetForegroundWindow = user32.SetForegroundWindow

    # Get the window placement
    place = WINDOWPLACEMENT()
    place.length = ctypes.sizeof(WINDOWPLACEMENT)
    GetWindowPlacement(hwnd, ctypes.byref(place))

    # Restore window if window is minimized
    SW_SHOWMINIMIZED = 2
    SW_RESTORE = 9
    if place.showCmd == SW_SHOWMINIMIZED:
        ShowWindow(hwnd, SW_RESTORE)

    # Set the window to the foreground
    SetForegroundWindow(hwnd)


def _control_window(
    name,
    cmd: Literal["activate", "close"],
    match_mode=TITLE_MATCH_MODE_DEFAULT,
):
    if sys.platform == "win32":
        from ctypes.wintypes import BOOL, HWND, LPARAM

        user32 = ctypes.windll.user32

        if match_mode == TITLE_MATCH_MODE_REGEX:
            patt = re.compile(name)

        hwnds = []  # matched hwnds

        active_hwnd = user32.GetForegroundWindow()

        def should_search_next(hwnd) -> bool:
            if cmd == "activate" and hwnd == active_hwnd:
                # Skip the active window and continue searching for the next match
                return True
            elif cmd == "close":
                # Keep searching
                return True
            else:
                # Stop searching
                return False

        def callback(hwnd, lParam):
            length = user32.GetWindowTextLengthW(hwnd) + 1
            buffer = ctypes.create_unicode_buffer(length)
            user32.GetWindowTextW(hwnd, buffer, length)
            win_title = str(buffer.value)
            if match_mode == TITLE_MATCH_MODE_EXACT and name == win_title:
                hwnds.append(hwnd)
                return should_search_next(hwnd=hwnd)
            elif match_mode == TITLE_MATCH_MODE_PARTIAL and name in win_title:
                hwnds.append(hwnd)
                return should_search_next(hwnd=hwnd)
            elif match_mode == TITLE_MATCH_MODE_START_WITH and win_title.startswith(
                name
            ):
                hwnds.append(hwnd)
                return should_search_next(hwnd=hwnd)
            elif match_mode == TITLE_MATCH_MODE_REGEX and re.search(patt, win_title):
                hwnds.append(hwnd)
                return should_search_next(hwnd=hwnd)
            else:
                return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(BOOL, HWND, LPARAM)
        user32.EnumWindows(WNDENUMPROC(callback), 42)

        for hwnd in hwnds:
            if cmd == "activate":
                if hwnd != active_hwnd:
                    _activate_window_win(hwnd)
                    break
            elif cmd == "close":
                WM_CLOSE = 0x10
                user32.PostMessageA(hwnd, WM_CLOSE, 0, 0)
            else:
                raise Exception("Invalid cmd parameter: %s" % cmd)
        return len(hwnds) > 0  # has any matches

    elif sys.platform == "linux":
        if not shutil.which("wmctrl"):
            logging.warning("Cannot %s window, wmctrl is not installed." % cmd)
            return

        if cmd == "activate":
            return 0 == subprocess.call(
                [
                    "bash",
                    os.path.abspath(
                        os.path.dirname(__file__)
                        + "/../../scripts/r/linux/activate_window_by_name.sh"
                    ),
                    name,
                ]
            )
        elif cmd == "close":
            return subprocess.call(["wmctrl", "-c", name]) == 0
        else:
            raise Exception("Invalid cmd parameter: %s" % cmd)

    elif sys.platform == "darwin":
        if cmd == "activate":
            return 0 == subprocess.call(
                [
                    "osascript",
                    "-e",
                    f"""set theTitle to "{name}"

tell application "System Events"
	set theProcesses to every process where background only is false
	repeat with theProcess in theProcesses
		tell theProcess
			repeat with theWindow in windows
				if name of theWindow contains theTitle then
					tell theWindow to perform action "AXRaise"
					set frontmost of theProcess to true
					return
				end if
			end repeat
		end tell
	end repeat
    error "not found"
end tell""",
                ]
            )
        elif cmd == "close":
            logging.warning("Cannot close window on macos")
        else:
            raise Exception("Invalid cmd parameter: %s" % cmd)

    return False


def activate_window_by_name(name, match_mode=TITLE_MATCH_MODE_DEFAULT):
    return _control_window(name=name, cmd="activate", match_mode=match_mode)


def close_window_by_name(name, match_mode=TITLE_MATCH_MODE_DEFAULT):
    return _control_window(name=name, cmd="close", match_mode=match_mode)
