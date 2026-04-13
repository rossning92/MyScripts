import ctypes
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from typing import Dict, List, Literal, Optional, Tuple

from .tmux import is_in_tmux

TITLE_MATCH_MODE_EXACT = 0
TITLE_MATCH_MODE_PARTIAL = 1
TITLE_MATCH_MODE_START_WITH = 2
TITLE_MATCH_MODE_REGEX = 3
TITLE_MATCH_MODE_DEFAULT = TITLE_MATCH_MODE_REGEX

WindowStatus = Literal["normal", "done", "error", "running"]

_WINDOW_STATUS_PRIORITY: Dict[WindowStatus, int] = {
    "done": 0,
    "error": 1,
    "running": 2,
    "normal": 3,
}

_WINDOW_STATUS_SYMBOLS: Dict[WindowStatus, str] = {
    "done": "✓✳",
    "running": "⧗⠂⠐",
}


class WindowItem:
    def __init__(self, id, title):
        self.id = id
        self.title = title

    def get_status(self, script_status: Dict[str, str]) -> WindowStatus:
        for status, symbols in _WINDOW_STATUS_SYMBOLS.items():
            if any(s in self.title for s in symbols):
                return status

        status = script_status.get(self.title, "normal")
        if status in ["done", "error", "running"]:
            return status  # type: ignore
        return "normal"

    def __str__(self):
        return self.title


def _get_windows_linux() -> List[WindowItem]:
    try:
        output = subprocess.check_output(
            ["wmctrl", "-l"], text=True, stderr=subprocess.DEVNULL
        )
        windows = []
        for line in output.strip().splitlines():
            # Format: 0x03400003  0 ross-pc title
            parts = line.split(None, 3)
            if len(parts) >= 3:
                window_id = parts[0]
                title = parts[3] if len(parts) == 4 else ""
                if title == "WinSwitcher":
                    continue
                windows.append(WindowItem(id=window_id, title=title))
        return windows
    except Exception:
        return []


def _get_windows_win(sort_by_title: bool = True) -> List[WindowItem]:
    """
    Get all top-level windows.
    """
    assert sys.platform == "win32"

    user32 = ctypes.windll.user32
    dwmapi = ctypes.windll.dwmapi
    GW_OWNER = 4
    GWL_EXSTYLE = -20
    WS_EX_TOOLWINDOW = 0x00000080
    DWMWA_CLOAKED = 14

    windows = []
    hwnd = user32.GetTopWindow(None)
    while hwnd:
        is_visible = user32.IsWindowVisible(hwnd)
        title_length = user32.GetWindowTextLengthW(hwnd)
        owner = user32.GetWindow(hwnd, GW_OWNER)
        ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)

        # Hidden by the system (like background Settings or Input Experience).
        cloaked = ctypes.c_int(0)
        dwmapi.DwmGetWindowAttribute(
            hwnd, DWMWA_CLOAKED, ctypes.byref(cloaked), ctypes.sizeof(cloaked)
        )

        if (
            is_visible
            and title_length > 0
            and owner == 0
            and not (ex_style & WS_EX_TOOLWINDOW)
            and cloaked.value == 0
        ):
            buff = ctypes.create_unicode_buffer(title_length + 1)
            user32.GetWindowTextW(hwnd, buff, title_length + 1)
            title = buff.value
            if title not in ["WinSwitcher", "Program Manager"]:
                windows.append(WindowItem(id=hwnd, title=title))

        hwnd = user32.GetWindow(hwnd, 2)

    if sort_by_title:
        windows.sort(key=lambda x: x.title.lower())

    return windows


def _get_windows_tmux() -> List[WindowItem]:
    try:
        output = subprocess.check_output(
            [
                "tmux",
                "list-windows",
                "-a",
                "-F",
                "#{session_name}:#{window_index}\t#{window_name}\t#{pane_title}",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        windows = []
        for line in output.strip().splitlines():
            if line:
                parts = line.split("\t", 2)
                assert len(parts) == 3
                target, name, pane_title = parts
                if name == "WinSwitcher":
                    continue

                title = f"{name} - {pane_title}" if pane_title else name
                windows.append(WindowItem(id=f"tmux:{target}", title=title))
        return windows
    except Exception:
        return []


def get_windows(
    sort_by_title: bool = True, script_status: Optional[Dict[str, str]] = None
) -> List[WindowItem]:
    if sys.platform == "linux":
        windows = _get_windows_linux()
    elif sys.platform == "win32":
        windows = _get_windows_win(sort_by_title=sort_by_title)
    elif is_in_tmux():
        windows = _get_windows_tmux()
    else:
        windows = []

    if script_status:
        windows.sort(
            key=lambda x: (
                _WINDOW_STATUS_PRIORITY.get(x.get_status(script_status), 3),
                x.title.lower() if sort_by_title else 0,
            )
        )

    return windows


def activate_window(win_id) -> Optional[str]:
    if isinstance(win_id, str) and win_id.startswith("tmux:"):
        target = win_id[len("tmux:") :]
        cp = subprocess.run(
            ["tmux", "select-window", "-t", target], capture_output=True, text=True
        )
        if cp.returncode != 0:
            return cp.stderr.splitlines()[0] if cp.stderr else "Error"
    elif sys.platform == "win32":
        user32 = ctypes.windll.user32

        hwnd = win_id
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE

        # Use the "Alt" key hack to bypass focus stealing restrictions
        # 0x12 is VK_MENU (Alt key)
        user32.keybd_event(0x12, 0, 0, 0)  # Alt Down
        user32.SetForegroundWindow(hwnd)
        user32.keybd_event(0x12, 0, 2, 0)  # Alt Up
    elif sys.platform == "linux":
        cp = subprocess.run(
            ["wmctrl", "-i", "-a", win_id], capture_output=True, text=True
        )
        if cp.returncode != 0:
            return cp.stderr.splitlines()[0] if cp.stderr else "Error"
    return None


def close_window(win_id) -> Optional[str]:
    if isinstance(win_id, str) and win_id.startswith("tmux:"):
        target = win_id[len("tmux:") :]
        cp = subprocess.run(
            ["tmux", "kill-window", "-t", target], capture_output=True, text=True
        )
        return cp.stderr.splitlines()[0] if cp.returncode != 0 and cp.stderr else None
    elif sys.platform == "win32":
        user32 = ctypes.windll.user32
        WM_CLOSE = 0x10
        user32.PostMessageW(win_id, WM_CLOSE, 0, 0)
        return None
    elif sys.platform == "linux":
        cp = subprocess.run(
            ["wmctrl", "-i", "-c", win_id], capture_output=True, text=True
        )
        return cp.stderr.splitlines()[0] if cp.returncode != 0 and cp.stderr else None
    return None


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
        if os.environ.get("XDG_SESSION_TYPE", None) == "wayland" and shutil.which(
            "swaymsg"
        ):
            if cmd == "activate":
                return 0 == subprocess.call(
                    [
                        "swaymsg",
                        f'[title="{name}"] focus',
                    ]
                )
            elif cmd == "close":
                return 0 == subprocess.call(
                    [
                        "swaymsg",
                        f'[title="{name}"] kill',
                    ]
                )
            else:
                raise Exception("Invalid cmd parameter: %s" % cmd)

        elif os.environ.get("DISPLAY", None) and shutil.which("wmctrl"):
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

        else:
            logging.warning("Cannot %s window, window manager is not supported" % cmd)
            return

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


def get_window_rect(
    window_name: Optional[str] = None,
) -> Optional[Tuple[int, int, int, int]]:
    if sys.platform == "linux":
        try:
            if window_name:
                cmd = ["xwininfo", "-name", window_name]
            else:
                window_id_proc = subprocess.run(
                    ["xdotool", "getactivewindow"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                window_id = window_id_proc.stdout.strip()
                cmd = ["xwininfo", "-id", window_id]
            proc = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError:
            return None
        output = proc.stdout

        x_match = re.search(r"Absolute upper-left X:\s+(-?\d+)", output)
        y_match = re.search(r"Absolute upper-left Y:\s+(-?\d+)", output)
        width_match = re.search(r"Width:\s+(\d+)", output)
        height_match = re.search(r"Height:\s+(\d+)", output)
        if not x_match or not y_match or not width_match or not height_match:
            raise Exception("Unable to parse xwininfo output")
        return (
            int(x_match.group(1)),
            int(y_match.group(1)),
            int(width_match.group(1)),
            int(height_match.group(1)),
        )
    else:
        raise NotImplementedError


def _set_window_rect_win(left: int, top: int, width: int, height: int, hwnd=None):
    if not sys.platform == "win32":
        raise Exception("The function is only supported on Windows")

    if hwnd is None:
        hwnd = ctypes.windll.user32.GetForegroundWindow()

    logging.debug("set window pos")
    ctypes.windll.user32.SetProcessDPIAware()
    ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    ctypes.windll.user32.SetForegroundWindow(hwnd)

    arect = ctypes.wintypes.RECT()
    DWMWA_EXTENDED_FRAME_BOUNDS = 9
    ret = ctypes.windll.dwmapi.DwmGetWindowAttribute(
        ctypes.wintypes.HWND(hwnd),
        ctypes.wintypes.DWORD(DWMWA_EXTENDED_FRAME_BOUNDS),
        ctypes.byref(arect),
        ctypes.sizeof(arect),
    )
    if ret != 0:
        raise Exception("DwmGetWindowAttribute failed")

    rect = ctypes.wintypes.RECT()
    ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
    dx = rect.left - arect.left
    dy = rect.top - arect.top
    dw = rect.right - arect.right - dx
    dh = rect.bottom - arect.bottom - dy
    ctypes.windll.user32.MoveWindow(
        hwnd, left + dx, top + dy, width + dw, height + dh, True
    )

    time.sleep(0.1)


def set_window_rect(left: int, top: int, width: int, height: int, hwnd=None):
    if sys.platform == "win32":
        _set_window_rect_win(left=left, top=top, width=width, height=height, hwnd=hwnd)
    else:
        subprocess.check_call(
            [
                "awesome-client",
                (
                    f'local awful = require("awful"); '
                    f"local c = client.focus; "
                    f"if c then "
                    f"c.floating = true; "
                    f"c:geometry({{ width = {width}, height = {height} }}); "
                    f"awful.placement.centered(c, {{ honor_workarea = true }}) "
                    f"end"
                ),
            ]
        )
    time.sleep(1)
