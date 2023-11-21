import subprocess
from typing import List

from utils.menu import Menu
from utils.menu.confirm import confirm


class ChocoPackageMenu(Menu):
    def __init__(self) -> None:
        self._items: List[str] = []
        super().__init__(items=self._items)
        self._refresh_packages()
        self.add_command(self._uninstall, hotkey="ctrl+u")

    def _refresh_packages(self):
        self._items[:] = subprocess.check_output(
            ["choco", "list", "--localonly"], universal_newlines=True
        ).splitlines()

    def _uninstall(self):
        selected = self.get_selected_item()
        if selected:
            package = selected.split()[0]
            if confirm(f"Confirm to uninstall `{package}`?"):
                self.call_func_without_curses(
                    lambda: subprocess.check_call(["choco", "uninstall", package, "-y"])
                )


if __name__ == "__main__":
    ChocoPackageMenu().exec()
