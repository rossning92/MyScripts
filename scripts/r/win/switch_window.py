import ctypes
import subprocess
import sys
import time
from typing import List

from utils.script.status import get_script_status
from utils.menu import Menu
from utils.tmux import is_in_tmux


class WindowItem:
    def __init__(self, id, title):
        self.id = id
        self.title = title

    def __str__(self):
        return self.title


def get_windows_linux() -> List[WindowItem]:
    try:
        output = subprocess.check_output(["wmctrl", "-l"], text=True)
        windows = []
        for line in output.strip().splitlines():
            # Format: 0x03400003  0 ross-pc title
            parts = line.split(None, 3)
            if len(parts) >= 3:
                window_id = parts[0]
                title = parts[3] if len(parts) == 4 else ""
                windows.append(WindowItem(id=window_id, title=title))
        return windows
    except Exception:
        return []


def get_windows_win() -> List[WindowItem]:
    """
    Get all top-level windows in Z-order (top to bottom).
    """

    assert sys.platform == "win32"

    user32 = ctypes.windll.user32

    windows = []
    hwnd = user32.GetTopWindow(None)
    while hwnd:
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                if user32.GetWindow(hwnd, 4) == 0:  # GW_OWNER = 4
                    style = user32.GetWindowLongW(hwnd, -20)  # GWL_EXSTYLE = -20
                    if not (style & 0x00000080):  # WS_EX_TOOLWINDOW = 0x00000080
                        buff = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buff, length + 1)
                        title = buff.value
                        if title != "switch_window":
                            windows.append(WindowItem(hwnd, title))
        hwnd = user32.GetWindow(hwnd, 2)  # GW_HWNDNEXT = 2
    return windows


def get_windows_tmux() -> List[WindowItem]:
    try:
        output = subprocess.check_output(
            [
                "tmux",
                "list-windows",
                "-a",
                "-F",
                "#{session_name}:#{window_index}\t#{window_name}",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        windows = []
        for line in output.strip().splitlines():
            if line:
                target, name = line.split("\t", 1)
                windows.append(WindowItem(id=f"tmux:{target}", title=name))
        return windows
    except Exception:
        return []


def get_windows() -> List[WindowItem]:
    windows = []
    if sys.platform == "linux":
        windows.extend(get_windows_linux())
    elif sys.platform == "win32":
        windows.extend(get_windows_win())

    if is_in_tmux():
        windows.extend(get_windows_tmux())
    return windows


class SwitchWindowMenu(Menu[WindowItem]):
    def __init__(self):
        super().__init__(prompt="activate", items=[])
        self.add_command(self.refresh_windows, hotkey="ctrl+r")
        self.refresh_windows()

        if sys.platform == "win32":
            user32 = ctypes.windll.user32
            self._my_hwnd = user32.FindWindowW(None, "switch_window")
        else:
            self._my_hwnd = None
        self._was_foreground = True

    def refresh_windows(self):
        self.items = get_windows()
        self.script_status = get_script_status()
        self.refresh()

    def on_enter_pressed(self):
        selected = self.get_selected_item()
        if selected:
            if isinstance(selected.id, str) and selected.id.startswith("tmux:"):
                target = selected.id[len("tmux:") :]
                subprocess.call(["tmux", "select-window", "-t", target])
                self.close()
            elif sys.platform == "win32":
                user32 = ctypes.windll.user32

                hwnd = selected.id
                if user32.IsIconic(hwnd):
                    user32.ShowWindow(hwnd, 9)  # SW_RESTORE

                # Use the "Alt" key hack to bypass focus stealing restrictions
                # 0x12 is VK_MENU (Alt key)
                user32.keybd_event(0x12, 0, 0, 0)  # Alt Down
                user32.SetForegroundWindow(hwnd)
                user32.keybd_event(0x12, 0, 2, 0)  # Alt Up

                self.clear_input()
            elif sys.platform == "linux":
                subprocess.call(["wmctrl", "-i", "-a", selected.id])
                self.close()

    def on_escape_pressed(self):
        self.clear_input()

    def on_idle(self):
        if sys.platform == "win32":
            user32 = ctypes.windll.user32

            hwnd = user32.GetForegroundWindow()
            is_foreground = hwnd == self._my_hwnd
            if is_foreground and not self._was_foreground:
                self.set_message(f"{time.strftime('%H:%M:%S')}: refresh window")
                self.refresh_windows()
            self._was_foreground = is_foreground
        else:
            # TODO: detect foreground window change on Linux if needed
            pass

    def get_item_color(self, item: WindowItem) -> str:
        if item.title in self.script_status:
            match = self.script_status[item.title]
            if match == "done":
                return "green"
            elif match == "error":
                return "red"
            elif match == "running":
                return "cyan"
        return "white"


if __name__ == "__main__":
    SwitchWindowMenu().exec()
