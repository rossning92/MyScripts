import json
import os
from typing import List, Optional

from _shutil import get_home_path
from _term import Menu


class Config:
    def __init__(self) -> None:
        self.cur_dir = get_home_path()
        self.selected_file = ""
        self.config_file = os.path.join(
            os.environ["MYSCRIPT_DATA_DIR"], "file_browser_config.json"
        )

    def load(self):
        with open(self.config_file, "r") as file:
            data = json.load(file)
        self.cur_dir = data["cur_dir"]
        self.selected_file = data["selected_file"]

    def save(self):
        data = {"cur_dir": self.cur_dir, "selected_file": self.selected_file}
        with open(self.config_file, "w") as f:
            json.dump(data, f, indent=4)


class FileBrowser(Menu):
    def __init__(self):
        self.config = Config()
        if os.path.exists(self.config.config_file):
            self.config.load()
        self.files: List[str] = []
        self.selected_file_full_path = None
        super().__init__(items=self.files)
        self.goto_directory(self.config.cur_dir, self.config.selected_file)

    def select_file(self):
        self.exec()
        return self.selected_file_full_path

    def goto_directory(self, d, file=""):
        self.config.cur_dir = d
        self.config.save()

        self.files[:] = [".."] + os.listdir(self.config.cur_dir)
        if file:
            self.set_input(file)
        else:
            self.clear_input()
        self.set_prompt(self.config.cur_dir)

    def on_enter_pressed(self):
        selected_file = self.get_selected_item()
        if selected_file:
            full_path = os.path.join(self.config.cur_dir, selected_file)
            if os.path.isdir(full_path):
                d = os.path.abspath(os.path.join(self.config.cur_dir, selected_file))
                self.goto_directory(d)
                return True
            elif os.path.isfile(full_path):
                self.selected_file_full_path = full_path
                self.config.selected_file = selected_file
                self.config.save()
                return super().on_enter_pressed()


def select_file() -> Optional[str]:
    return FileBrowser().select_file()
