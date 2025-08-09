import subprocess

from scripting.path import get_script_alias
from utils.menu import Menu


class _Window:
    def __init__(self, name: str):
        self.name = name
        self.alias = get_script_alias(name)

    def __str__(self):
        return f"[{self.alias}]\t{self.name}"


class SwitchWindowMenu(Menu[_Window]):
    def __init__(self, **kwargs):
        result = subprocess.run(
            [
                "tmux",
                "list-windows",
                "-a",
                "-f",
                "#{?window_active,0,1}",  # filter out the current window
                "-F",
                "#{window_name}",
            ],
            capture_output=True,
            text=True,
        )
        windows = [_Window(name) for name in result.stdout.strip().splitlines()]
        super().__init__(prompt="select window", items=windows, **kwargs)

    def match_item(self, keyword: str, item: _Window, index: int) -> int:
        if len(keyword) == 0 or item.alias.startswith(keyword):
            return 1
        else:
            return 0

    def on_enter_pressed(self):
        self.switch_to_selected_window()

    def on_matched_items_updated(self):
        if self.get_row_count() == 1:
            self.switch_to_selected_window()

    def switch_to_selected_window(self):
        window = self.get_selected_item()
        if window:
            subprocess.run(["tmux", "select-window", "-t", window.name])
            self.close()


if __name__ == "__main__":
    SwitchWindowMenu().exec()
