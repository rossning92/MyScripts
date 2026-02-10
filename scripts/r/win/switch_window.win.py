import ctypes
import time
from typing import List

from utils.menu import Menu

user32 = ctypes.windll.user32


class WindowItem:
    def __init__(self, hwnd, title):
        self.hwnd = hwnd
        self.title = title

    def __str__(self):
        return self.title


def get_windows() -> List[WindowItem]:
    """
    Get all top-level windows in Z-order (top to bottom).
    """
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


class SwitchWindowMenu(Menu):
    def __init__(self):
        super().__init__(prompt="switch window", items=[])
        self.add_command(self.refresh_windows, hotkey="ctrl+r")
        self.refresh_windows()

        self._my_hwnd = user32.FindWindowW(None, "switch_window")
        self._was_foreground = True

    def refresh_windows(self):
        self.items = get_windows()
        self.refresh()

    def on_enter_pressed(self):
        selected = self.get_selected_item()
        if selected:
            hwnd = selected.hwnd
            if user32.IsIconic(hwnd):
                user32.ShowWindow(hwnd, 9)  # SW_RESTORE

            # Use the "Alt" key hack to bypass focus stealing restrictions
            # 0x12 is VK_MENU (Alt key)
            user32.keybd_event(0x12, 0, 0, 0)  # Alt Down
            user32.SetForegroundWindow(hwnd)
            user32.keybd_event(0x12, 0, 2, 0)  # Alt Up

            self.clear_input()

    def on_escape_pressed(self):
        self.clear_input()

    def on_idle(self):
        hwnd = user32.GetForegroundWindow()
        is_foreground = hwnd == self._my_hwnd
        if is_foreground and not self._was_foreground:
            self.set_message(f"{time.strftime('%H:%M:%S')}: refresh window")
            self.refresh_windows()
        self._was_foreground = is_foreground


if __name__ == "__main__":
    SwitchWindowMenu().exec()
