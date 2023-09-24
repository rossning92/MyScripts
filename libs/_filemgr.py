import json
import os
from typing import List, Optional

from _shutil import get_home_path, shell_open
from _term import Menu


class _Config:
    def __init__(self) -> None:
        self.cur_dir = get_home_path()
        self.selected_file = ""
        self.config_file = os.path.join(
            os.environ["MY_DATA_DIR"], "filemgr_config.json"
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


class _File:
    def __init__(self, name: str, is_dir: bool) -> None:
        self.name = name
        self.is_dir = is_dir

    def __str__(self) -> str:
        if self.is_dir:
            return f"[ {self.name} ]"
        else:
            return self.name


class FileManager(Menu[_File]):
    def __init__(self, goto=None):
        self.config = _Config()
        if os.path.exists(self.config.config_file):
            self.config.load()
        self.files: List[_File] = []
        self.selected_file_full_path = None
        self.select_file_mode = False

        super().__init__(items=self.files)

        if goto is not None:
            if os.path.isdir(goto):
                self.goto_directory(goto)
            else:
                self.goto_directory(os.path.dirname(goto), os.path.basename(goto))
        else:
            self.goto_directory(self.config.cur_dir, self.config.selected_file)

        self.add_hotkey("shift+h", self._goto_home)
        self.add_hotkey("shift+n", self._rename_file)

    def _goto_home(self):
        self.goto_directory(get_home_path())

    def _rename_file(self):
        selected = self.get_selected_item()
        if selected:
            w = Menu(label="New name", text=selected.name)
            w.exec()
            new_name = w.get_input()
            if not new_name:
                return

            src = os.path.abspath(os.path.join(self.config.cur_dir, selected.name))
            dest = os.path.abspath(os.path.join(self.config.cur_dir, new_name))

            os.rename(src, dest)

            self.refresh()

    def select_file(self):
        self.select_file_mode = True
        self.exec()
        return self.selected_file_full_path

    def refresh(self):
        self.goto_directory(self.config.cur_dir)

    def goto_directory(self, directory, file=""):
        if not os.path.isdir(directory):
            directory = get_home_path()

        self.config.cur_dir = directory
        self.config.save()

        # Enumerate files
        self.files.clear()
        self.files.append(_File("..", is_dir=True))
        dirs = []
        files = []
        for file in os.listdir(self.config.cur_dir):
            full_path = os.path.join(self.config.cur_dir, file)
            if os.path.isdir(full_path):
                dirs.append(_File(file, is_dir=True))
            else:
                files.append(_File(file, is_dir=False))
        dirs.sort(key=lambda x: x.name)
        files.sort(key=lambda x: x.name)
        self.files.extend(dirs)
        self.files.extend(files)

        self.clear_input()
        self.set_prompt(self.config.cur_dir)

    def on_enter_pressed(self):
        selected = self.get_selected_item()
        if selected:
            full_path = os.path.join(self.config.cur_dir, selected.name)
            if os.path.isdir(full_path):
                d = os.path.abspath(os.path.join(self.config.cur_dir, selected.name))
                self.goto_directory(d)
                return True
            elif os.path.isfile(full_path):
                self.selected_file_full_path = full_path
                self.config.selected_file = selected.name
                self.config.save()
                if self.select_file_mode:
                    return super().on_enter_pressed()
                else:
                    shell_open(full_path)
                    return True


def select_file() -> Optional[str]:
    return FileManager().select_file()
