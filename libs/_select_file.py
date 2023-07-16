import glob
import os
from typing import Optional

from _shutil import get_home_path
from _term import Menu


class FileBrowser(Menu):
    def __init__(self):
        self.cur_dir = get_home_path()
        self.files = os.listdir(self.cur_dir)
        self.selected_file = None
        super().__init__(items=self.files, label=self.cur_dir)

    def select_file(self):
        self.exec()
        return self.selected_file

    def on_char(self, ch):
        return super().on_char(ch)

    def on_enter_pressed(self):
        selected = self.get_selected_item()
        if selected:
            full_path = os.path.join(self.cur_dir, selected)
            if os.path.isdir(full_path):
                self.cur_dir = os.path.join(self.cur_dir, selected)
                self.files[:] = os.listdir(self.cur_dir)
                self.clear_input()
                self.input_.label = self.cur_dir
                return True
            elif os.path.isfile(full_path):
                self.selected_file = full_path
                return super().on_enter_pressed()


def select_file() -> Optional[str]:
    return FileBrowser().select_file()
