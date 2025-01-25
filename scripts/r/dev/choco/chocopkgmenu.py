import subprocess
from typing import List, Optional

from utils.menu import Menu


class ChocoPackageMenu(Menu):
    def __init__(self) -> None:
        self._items: List[str] = []
        super().__init__(items=self._items)
        self._refresh_packages()

    def _refresh_packages(self):
        self._items[:] = subprocess.check_output(
            ["choco", "list"], universal_newlines=True
        ).splitlines()

    def get_selected_package(self) -> Optional[str]:
        selected = self.get_selected_item()
        if selected:
            package = selected.split()[0]
            return package
        else:
            return None
