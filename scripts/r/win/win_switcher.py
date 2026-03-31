import ctypes
import subprocess
import sys
import time
from typing import Dict, List, Literal, Optional

from utils.menu import Menu
from utils.notify import get_notifications
from utils.tmux import is_in_tmux

_WINDOW_CLOSE_WAIT_SECONDS = 1.0
_AUTO_REFRESH_INTERVAL_SECONDS = 2.0

WindowStatus = Literal["normal", "done", "error", "running"]

_STATUS_COLOR_MAPPING: Dict[WindowStatus, str] = {
    "done": "green",
    "error": "red",
    "running": "cyan",
}

_WINDOW_STATUS_PRIORITY: Dict[WindowStatus, int] = {
    "done": 0,
    "error": 1,
    "running": 2,
    "normal": 3,
}


class WindowItem:
    def __init__(self, id, title):
        self.id = id
        self.title = title

    def get_status(self, script_status: Dict[str, str]) -> WindowStatus:
        if "✓" in self.title:
            return "done"
        if "⧗" in self.title:
            return "running"
        status = script_status.get(self.title, "normal")
        if status in ["done", "error", "running"]:
            return status  # type: ignore
        return "normal"

    def __str__(self):
        return self.title


def get_windows_linux() -> List[WindowItem]:
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


def get_windows_win(sort_by_title: bool = True) -> List[WindowItem]:
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


def get_windows_tmux() -> List[WindowItem]:
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
        windows = get_windows_linux()
    elif sys.platform == "win32":
        windows = get_windows_win(sort_by_title=sort_by_title)
    elif is_in_tmux():
        windows = get_windows_tmux()
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


class WinSwitcherMenu(Menu[WindowItem]):
    def __init__(self):
        super().__init__(prompt="activate", items=[], line_number=False)
        self.__auto_refresh_enabled = True
        self.__auto_refresh_last_time = 0.0
        self.__sort_by_title = False
        self.script_status: Dict[str, str] = {}
        self.add_command(self.__refresh_windows, hotkey="ctrl+r")
        self.add_command(self.__close_window, hotkey="delete")
        self.add_command(self.__close_window, hotkey="ctrl+k")
        self.add_command(self.__toggle_sort_mode, hotkey="ctrl+t")
        self.__refresh_windows()

    def __toggle_sort_mode(self):
        self.__sort_by_title = not self.__sort_by_title
        self.__refresh_windows()

    def __refresh_windows(self, message: Optional[str] = None):
        notifications = get_notifications()
        self.script_status = {
            n["app"]: n.get("hint")
            for n in (notifications or [])
            if isinstance(n, dict) and isinstance(n.get("app"), str)
        }
        self.items = get_windows(
            sort_by_title=self.__sort_by_title, script_status=self.script_status
        )

        if message:
            self.set_message(message)
        else:
            self.set_message(f"{time.monotonic():.1f} refreshed")
        self.refresh()

    def __activate_window(self, win_id):
        if isinstance(win_id, str) and win_id.startswith("tmux:"):
            target = win_id[len("tmux:") :]
            cp = subprocess.run(
                ["tmux", "select-window", "-t", target], capture_output=True, text=True
            )
            if cp.returncode != 0:
                self.set_message(cp.stderr.splitlines()[0] if cp.stderr else "Error")
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
                self.set_message(cp.stderr.splitlines()[0] if cp.stderr else "Error")

    def __close_window_by_id(self, win_id) -> Optional[str]:
        if isinstance(win_id, str) and win_id.startswith("tmux:"):
            target = win_id[len("tmux:") :]
            cp = subprocess.run(
                ["tmux", "kill-window", "-t", target], capture_output=True, text=True
            )
            return (
                cp.stderr.splitlines()[0] if cp.returncode != 0 and cp.stderr else None
            )
        elif sys.platform == "win32":
            user32 = ctypes.windll.user32
            WM_CLOSE = 0x10
            user32.PostMessageW(win_id, WM_CLOSE, 0, 0)
            return None
        elif sys.platform == "linux":
            cp = subprocess.run(
                ["wmctrl", "-i", "-c", win_id], capture_output=True, text=True
            )
            return (
                cp.stderr.splitlines()[0] if cp.returncode != 0 and cp.stderr else None
            )
        return None

    def __close_window(self):
        selected_items = list(self.get_selected_items())
        if not selected_items:
            return

        error = None
        win_ids_to_wait = []
        for selected in selected_items:
            err = self.__close_window_by_id(selected.id)
            if err:
                error = err
            else:
                win_ids_to_wait.append(selected.id)

        # Wait briefly for the windows to close
        if win_ids_to_wait:
            timeout = time.time() + _WINDOW_CLOSE_WAIT_SECONDS
            while time.time() < timeout:
                current_ids = {w.id for w in get_windows(sort_by_title=False)}
                win_ids_to_wait = [wid for wid in win_ids_to_wait if wid in current_ids]
                if not win_ids_to_wait:
                    break
                time.sleep(0.1)

        self.set_multi_select(False)
        self.__refresh_windows(message=error)

    def on_enter_pressed(self):
        selected = self.get_selected_item()
        if selected:
            self.__activate_window(selected.id)

    def on_char(self, ch):
        if isinstance(ch, str) and ch.isdigit():
            index = int(ch) - 1
            if 0 <= index <= 8:
                item_indices = list(self.get_item_indices())
                if index < len(item_indices):
                    self.__activate_window(self.items[item_indices[index]].id)
                    return True
        return super().on_char(ch)

    def on_focus_gained(self):
        self.__refresh_windows()
        self.__auto_refresh_enabled = True
        self.__auto_refresh_last_time = time.time()

    def on_focus_lost(self):
        self.__auto_refresh_enabled = False

    def on_idle(self):
        now = time.time()
        if (
            self.__auto_refresh_enabled
            and now > self.__auto_refresh_last_time + _AUTO_REFRESH_INTERVAL_SECONDS
        ):
            self.__auto_refresh_last_time = now
            self.__refresh_windows()

    def on_escape_pressed(self):
        self.clear_input()

    def get_item_text(self, item: WindowItem) -> str:
        text = super().get_item_text(item)
        item_indices = self.get_item_indices()
        for i in range(min(9, len(item_indices))):
            if self.items[item_indices[i]] == item:
                return f"[{i + 1}] {text}"
        return "    " + text

    def get_item_color(self, item: WindowItem) -> str:
        status = item.get_status(self.script_status)
        return _STATUS_COLOR_MAPPING.get(status, "white")


if __name__ == "__main__":
    WinSwitcherMenu().exec()
