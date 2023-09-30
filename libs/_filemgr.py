import glob
import json
import os
from typing import Dict, List, Optional

from _menu import Menu
from _shutil import get_home_path, shell_open


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
            return f"[ {self.name} ] ->"
        else:
            return self.name


class FileManager(Menu[_File]):
    SELECT_MODE_NONE = 0
    SELECT_MODE_FILE = 1
    SELECT_MODE_DIRECTORY = 2

    def __init__(self, goto=None):
        self._config = _Config()
        if os.path.exists(self._config.config_file):
            self._config.load()

        self._files: List[_File] = []
        self._selected_full_path = None
        self._select_mode = FileManager.SELECT_MODE_NONE

        super().__init__(items=self._files)

        self.add_hotkey("shift+h", self._goto_home)
        self.add_hotkey("shift+n", self._rename_file)
        self.add_hotkey("shift+r", self._list_files_recursively)
        self.add_hotkey("left", self._goto_parent_directory)
        self.add_hotkey("right", self._goto_selected_directory)
        self._selected_file_dict: Dict[str, str] = {}

        if goto is not None:
            if goto == ".":
                self.goto_directory(os.getcwd())
            elif os.path.isdir(goto):
                self.goto_directory(goto)
            else:
                self.goto_directory(os.path.dirname(goto), os.path.basename(goto))
        else:
            self.goto_directory(self._config.cur_dir, self._config.selected_file)

    def _goto_home(self):
        self.goto_directory(get_home_path())

    def _goto_parent_directory(self):
        # If current directory is not file system root
        parent = os.path.dirname(self._config.cur_dir)
        if parent != self._config.cur_dir:
            self.goto_directory(parent, os.path.basename(self._config.cur_dir))

    def _goto_selected_directory(self):
        selected = self.get_selected_item()
        if selected:
            full_path = os.path.join(self._config.cur_dir, selected.name)
            if os.path.isdir(full_path):
                d = os.path.abspath(os.path.join(self._config.cur_dir, selected.name))
                self.goto_directory(d)

    def _list_files_recursively(self):
        self.goto_directory(self._config.cur_dir, list_file_recursively=True)

    def _rename_file(self):
        selected = self.get_selected_item()
        if selected:
            w = Menu(label="New name", text=selected.name)
            w.exec()
            new_name = w.get_input()
            if not new_name:
                return

            src = os.path.abspath(os.path.join(self._config.cur_dir, selected.name))
            dest = os.path.abspath(os.path.join(self._config.cur_dir, new_name))

            os.rename(src, dest)

            self.refresh()

    def select_file(self):
        self._select_mode = FileManager.SELECT_MODE_FILE
        self.exec()
        return self._selected_full_path

    def select_directory(self):
        self._select_mode = FileManager.SELECT_MODE_DIRECTORY
        self.exec()
        return self._selected_full_path

    def refresh(self):
        self.goto_directory(self._config.cur_dir)

    def goto_directory(
        self,
        directory: str,
        selected_file: Optional[str] = None,
        list_file_recursively=False,
    ):
        # Remember last selected file
        if directory != self._config.cur_dir:
            selected_item = self.get_selected_item()
            if selected_item is not None:
                self._selected_file_dict[self._config.cur_dir] = selected_item.name

        # Change directory
        if not os.path.isdir(directory):
            directory = get_home_path()

        if directory != self._config.cur_dir:
            self._config.cur_dir = directory
            self._config.save()

        # Enumerate files
        self._list_files(list_file_recursively=list_file_recursively)

        # Clear input
        self.clear_input()
        self.set_prompt(self._config.cur_dir)

        # Set last selected file
        if selected_file is None and self._config.cur_dir in self._selected_file_dict:
            selected_file = self._selected_file_dict[self._config.cur_dir]
        if selected_file is not None:
            try:
                selected_row = next(
                    i
                    for i, file in enumerate(self._files)
                    if file.name == selected_file
                )
                self.set_selected_row(selected_row)
            except StopIteration:
                pass

    def _list_files(self, list_file_recursively=False):
        self._files.clear()

        try:
            if list_file_recursively:
                files = list(
                    glob.glob(
                        os.path.join(self._config.cur_dir, "**", "*"), recursive=True
                    )
                )
                files = [file for file in files if os.path.isfile(file)]
                files = [
                    file.replace(self._config.cur_dir + os.path.sep, "").replace(
                        "\\", "/"
                    )
                    for file in files
                ]
                self._files.extend([_File(file, is_dir=False) for file in files])

            else:
                dirs = []
                files = []
                for file in os.listdir(self._config.cur_dir):
                    full_path = os.path.join(self._config.cur_dir, file)
                    if os.path.isdir(full_path):
                        dirs.append(_File(file, is_dir=True))
                    else:
                        files.append(_File(file, is_dir=False))
                dirs.sort(key=lambda x: x.name)
                files.sort(key=lambda x: x.name)
                self._files.extend(dirs)
                self._files.extend(files)

        except PermissionError:
            pass

    def on_exit(self):
        selected = self.get_selected_item()
        if selected:
            self._config.selected_file = selected.name
            self._config.save()

    def on_enter_pressed(self):
        if self._select_mode == FileManager.SELECT_MODE_DIRECTORY:
            self._selected_full_path = self._config.cur_dir
            return super().on_enter_pressed()

        else:
            selected = self.get_selected_item()
            if selected:
                full_path = os.path.join(self._config.cur_dir, selected.name)
                if os.path.isdir(full_path):
                    d = os.path.abspath(
                        os.path.join(self._config.cur_dir, selected.name)
                    )
                    self.goto_directory(d)
                    return True
                elif os.path.isfile(full_path):
                    self._selected_full_path = full_path
                    if self._select_mode == FileManager.SELECT_MODE_FILE:
                        return super().on_enter_pressed()
                    else:
                        shell_open(full_path)
                        return True
