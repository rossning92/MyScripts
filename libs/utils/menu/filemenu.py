import glob
import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Literal, Optional

from _shutil import get_home_path

from utils.clip import set_clip
from utils.editor import open_code_editor
from utils.fileutils import human_readable_size
from utils.platform import is_termux
from utils.shutil import shell_open

from . import Menu
from .confirmmenu import confirm
from .inputmenu import InputMenu


def get_download_dir():
    if is_termux():
        return os.path.join(get_home_path(), "storage", "downloads")
    else:
        return os.path.join(get_home_path(), "Downloads")


class _Config:
    def __init__(self) -> None:
        self.cur_dir: str = get_home_path()
        self.selected_file = ""
        self.path_history: List[str] = [get_home_path(), get_download_dir()]
        self.sort_by: Literal["name", "mtime"] = "name"

    def load(self, config_file: str):
        with open(config_file, "r") as file:
            data = json.load(file)

        for key, value in data.items():
            if key in self.__dict__:
                if not isinstance(value, type(self.__dict__[key])):
                    raise Exception(f"Invalid type for `{key}`")
                setattr(self, key, value)

    def save(self, config_file: str):
        data = {
            key: value
            for key, value in self.__dict__.items()
            if not key.startswith("_")
        }
        with open(config_file, "w") as f:
            json.dump(data, f, indent=4)


def get_dir_size(full_path: str) -> int:
    return sum(f.stat().st_size for f in Path(full_path).glob("**/*") if f.is_file())


class _File:
    def __init__(
        self,
        name: str,
        is_dir: bool,
        full_path: str,
        file_size: int,
        show_size: bool,
        show_mtime: bool,
        relative_path=False,
    ) -> None:
        self.name = name
        self.is_dir = is_dir
        self.full_path = full_path
        self.file_size = file_size
        self.relative_path = relative_path
        self.show_size = show_size
        self.show_mtime = show_mtime

    def __str__(self) -> str:
        s = ""

        # Size column
        if self.show_size:
            size = human_readable_size(self.file_size) if not self.is_dir else ""
            s += f"{size:>6}  "

        # Modified time column
        if self.show_size:
            mtime = os.path.getmtime(self.full_path)
            formatted_time = datetime.fromtimestamp(mtime).strftime("%y-%m-%d %H:%M")
            s += formatted_time + "  "

        # Name column
        s += self.name

        return s


class FileMenu(Menu[_File]):
    SELECT_MODE_NONE = 0
    SELECT_MODE_FILE = 1
    SELECT_MODE_DIRECTORY = 2

    def __init__(
        self,
        goto=None,
        save_states=True,
        prompt=None,
        recursive=False,
        show_mtime=True,
        show_size=True,
        allow_cd=True,
    ):
        self.__config_file = os.path.join(
            os.environ["MY_DATA_DIR"], "filemgr_config.json"
        )
        self.__config = _Config()
        if os.path.exists(self.__config_file):
            self.__config.load(self.__config_file)

        self.__files: List[_File] = []
        self.__last_copy_to_path: Optional[str] = None
        self.__prompt: Optional[str] = prompt
        self.__save_states: bool = save_states if goto is None else False
        self.__select_mode: int = FileMenu.SELECT_MODE_NONE
        self.__selected_file_dict: Dict[str, str] = {}
        self.__selected_files_full_path: List[str] = []
        self.__show_mtime = show_mtime
        self.__show_size = show_size
        self.__allow_cd = allow_cd

        super().__init__(items=self.__files, wrap_text=True)

        self.add_command(self.copy_to, hotkey="alt+c")

        self.add_command(self._copy_file_full_path, hotkey="alt+y")
        self.add_command(self._create_new_dir, hotkey="ctrl+n")
        self.add_command(self._delete_files, hotkey="ctrl+k")
        self.add_command(self._edit_text_file, hotkey="ctrl+e")
        self.add_command(self._get_dir_size, hotkey="alt+s")
        self.add_command(self._list_files_recursively, hotkey="ctrl+l")
        self.add_command(self._move_to, hotkey="alt+m")
        self.add_command(self._refresh_cur_dir, hotkey="ctrl+r")
        self.add_command(self._rename_file, hotkey="alt+n")
        self.add_command(self._reveal_in_file_explorer, hotkey="ctrl+o")
        self.add_command(self._run_script, hotkey="!")
        self.add_command(lambda: self.sort_by("name"), name="sort_by_name")
        self.add_command(lambda: self.sort_by("mtime"), name="sort_by_mtime")

        if allow_cd:
            self.add_command(self._goto_parent_directory, hotkey="left")
            self.add_command(self._goto_selected_directory, hotkey="right")
            self.add_command(self._goto, hotkey="ctrl+g")

        if goto is not None:
            if goto == ".":
                self.goto_directory(os.getcwd(), list_file_recursively=recursive)
            elif os.path.isdir(goto):
                self.goto_directory(goto, list_file_recursively=recursive)
            else:
                self.goto_directory(
                    os.path.dirname(goto),
                    os.path.basename(goto),
                    list_file_recursively=recursive,
                )
        else:
            self.goto_directory(
                self.__config.cur_dir,
                self.__config.selected_file,
                list_file_recursively=recursive,
            )

    def get_item_color(self, item: _File) -> str:
        return "blue" if item.is_dir else "white"

    def _reveal_in_file_explorer(self):
        shell_open(self.get_cur_dir())

    def get_cur_dir(self) -> str:
        return self.__config.cur_dir

    def _create_new_dir(self):
        new_dir_name = InputMenu(prompt="create directory").request_input()
        if new_dir_name:
            current_dir = self.get_cur_dir()
            new_dir_path = os.path.join(current_dir, new_dir_name)
            os.makedirs(new_dir_path, exist_ok=True)
            self.goto_directory(new_dir_path)

    def _copy_file_full_path(self):
        file_full_path = self.get_selected_file_full_path()
        if file_full_path is not None:
            set_clip(file_full_path)
            self.set_message(f"Path copied: {file_full_path}")

    def _get_dir_size(self):
        for file in self.items:
            if file.is_dir:
                file.file_size = get_dir_size(file.full_path)
        self.update_screen()

    def _edit_text_file(self):
        file_full_path = self.get_selected_file_full_path()
        if file_full_path is not None:
            self.call_func_without_curses(lambda: open_code_editor(file_full_path))

    def _delete_files(self):
        files = self.get_selected_files()

        if len(files) > 0:
            if len(files) == 1:
                question = f'Delete "{files[0]}"?'
            else:
                question = f"Delete {len(files)} files?"
            if confirm(question):
                for file_full_path in files:
                    if os.path.isdir(file_full_path):
                        shutil.rmtree(file_full_path)
                    else:
                        os.remove(file_full_path)
                self._refresh_cur_dir()

            self.update_screen()

    def _copy_or_move_files(self, file: Optional[str] = None, copy=True):
        files: List[str] = []
        if file is not None:
            files.append(file)
        else:
            files = self.get_selected_files()

        if len(files) > 0:
            filemgr = FileMenu(
                goto=(
                    self.__last_copy_to_path
                    if self.__last_copy_to_path is not None
                    else self.get_cur_dir()
                ),
                prompt="%s to" % ("copy" if copy else "move"),
                save_states=False,
            )
            dest_dir = filemgr.select_directory()
            if dest_dir is not None:
                self.__last_copy_to_path = dest_dir
                for src in files:
                    if copy:
                        if os.path.isdir(src):
                            shutil.copytree(
                                src, os.path.join(dest_dir, os.path.basename(src))
                            )
                        else:
                            shutil.copy(src, dest_dir)
                    else:
                        shutil.move(src, dest_dir)

                self.goto_directory(dest_dir, selected_file=os.path.basename(files[0]))

    def copy_to(self, file: Optional[str] = None):
        self._copy_or_move_files(file=file, copy=True)

    def _move_to(self):
        self._copy_or_move_files(copy=False)

    def _goto_parent_directory(self):
        # If current directory is not file system root
        parent = os.path.dirname(self.get_cur_dir())
        if parent != self.get_cur_dir():
            self.goto_directory(parent, os.path.basename(self.get_cur_dir()))

    def _goto_selected_directory(self):
        selected = self.get_selected_item()
        if selected:
            full_path = os.path.join(self.get_cur_dir(), selected.name)
            if selected.relative_path:
                if os.path.isfile(full_path):
                    self.goto_directory(
                        os.path.dirname(full_path), os.path.basename(full_path)
                    )
                elif os.path.isdir(full_path):
                    self.goto_directory(full_path)

            else:
                full_path = os.path.join(self.get_cur_dir(), selected.name)
                if os.path.isdir(full_path):
                    d = os.path.abspath(os.path.join(self.get_cur_dir(), selected.name))
                    self.goto_directory(d)

    def _list_files_recursively(self):
        self.set_message("Find files recursively.")
        self.goto_directory(self.get_cur_dir(), list_file_recursively=True)

    def _rename_file(self):
        selected = self.get_selected_item()
        if selected:
            new_name = InputMenu(prompt="rename", text=selected.name).request_input()
            if not new_name:
                return

            src = os.path.abspath(os.path.join(self.get_cur_dir(), selected.name))
            dest = os.path.abspath(os.path.join(self.get_cur_dir(), new_name))

            os.rename(src, dest)

            self._refresh_cur_dir()

    def _goto(self):
        path = InputMenu(
            items=self.__config.path_history,
            prompt="goto",
            return_selection_if_empty=True,
            item_hotkey={
                get_download_dir(): "ctrl+d",
                get_home_path(): "ctrl+h",
            },
        ).request_input()
        if path is not None and os.path.isdir(path):
            self.goto_directory(path)

    def select_file(self) -> Optional[str]:
        self.__select_mode = FileMenu.SELECT_MODE_FILE
        self.exec()
        return (
            self.__selected_files_full_path[0]
            if len(self.__selected_files_full_path) > 0
            else None
        )

    def select_files(self) -> List[str]:
        self.__select_mode = FileMenu.SELECT_MODE_FILE
        self.exec()
        return self.__selected_files_full_path

    def select_directory(self) -> Optional[str]:
        self.__select_mode = FileMenu.SELECT_MODE_DIRECTORY
        self.exec()
        return (
            self.__selected_files_full_path[0]
            if len(self.__selected_files_full_path) > 0
            else None
        )

    def _refresh_cur_dir(self):
        self.goto_directory(self.get_cur_dir())
        self.set_multi_select(False)

    def _add_path_to_history(self, directory: str):
        MAX_PATH_IN_HISTORY = 20
        try:
            self.__config.path_history.remove(directory)
        except ValueError:
            pass
        finally:
            self.__config.path_history.insert(0, directory)
        if len(self.__config.path_history) > MAX_PATH_IN_HISTORY:
            self.__config.path_history.pop()

    def goto_directory(
        self,
        directory: str,
        selected_file: Optional[str] = None,
        list_file_recursively=False,
    ):
        self.set_message(None)

        # Remember last selected file
        if directory != self.get_cur_dir():
            selected_item = self.get_selected_item()
            if selected_item is not None:
                self.__selected_file_dict[self.get_cur_dir()] = selected_item.name

        # Change directory
        if not os.path.isdir(directory):
            directory = get_home_path()

        self._add_path_to_history(directory)

        # Save config
        if directory != self.get_cur_dir():
            self.__config.cur_dir = directory
            if self.__save_states:
                self.__config.save(self.__config_file)

        # Enumerate files
        self._list_files(list_file_recursively=list_file_recursively)

        # Clear input
        self.clear_input()

        # Update prompt
        if self.__allow_cd:
            self.set_prompt(
                f"{self.__prompt} ({self.get_cur_dir()})"
                if self.__prompt
                else self.get_cur_dir()
            )
        elif self.__prompt:
            self.set_prompt(self.__prompt)

        # Set last selected file
        if selected_file is None and self.get_cur_dir() in self.__selected_file_dict:
            selected_file = self.__selected_file_dict[self.get_cur_dir()]
        if selected_file is not None:
            try:
                selected_row = next(
                    i
                    for i, file in enumerate(self.__files)
                    if file.name == selected_file
                )
                self.set_selected_row(selected_row)
            except StopIteration:
                pass

    def _list_files(self, list_file_recursively=False):
        self.__files.clear()

        if list_file_recursively:
            files = list(
                glob.glob(os.path.join(self.get_cur_dir(), "**", "*"), recursive=True)
            )
            files = [file for file in files if os.path.isfile(file)]
            files = [
                file.replace(self.get_cur_dir() + os.path.sep, "").replace("\\", "/")
                for file in files
            ]
            self.__files.extend(
                [
                    _File(
                        file,
                        is_dir=False,
                        full_path=self.get_cur_dir() + "/" + file,
                        file_size=os.path.getsize(
                            os.path.join(self.get_cur_dir(), file)
                        ),
                        relative_path=True,
                        show_mtime=self.__show_mtime,
                        show_size=self.__show_size,
                    )
                    for file in files
                ]
            )

        else:
            dir_items = []
            file_items = []

            try:
                files = os.listdir(self.get_cur_dir())
            except Exception as ex:
                logging.error(str(ex))
                files = []

            for file in files:
                try:
                    full_path = os.path.join(self.get_cur_dir(), file)
                    if os.path.isdir(full_path):
                        dir_items.append(
                            _File(
                                file,
                                full_path=full_path,
                                file_size=0,
                                is_dir=True,
                                show_mtime=self.__show_mtime,
                                show_size=self.__show_size,
                            )
                        )
                    else:
                        file_items.append(
                            _File(
                                file,
                                full_path=full_path,
                                file_size=os.path.getsize(full_path),
                                is_dir=False,
                                show_mtime=self.__show_mtime,
                                show_size=self.__show_size,
                            )
                        )

                except Exception as ex:
                    logging.error(str(ex))

            if self.__config.sort_by == "name":
                dir_items.sort(key=lambda x: x.name)
                file_items.sort(key=lambda x: x.name)
            elif self.__config.sort_by == "mtime":
                dir_items.sort(
                    key=lambda x: os.path.getmtime(x.full_path), reverse=True
                )
                file_items.sort(
                    key=lambda x: os.path.getmtime(x.full_path), reverse=True
                )

            self.__files.extend(dir_items)
            self.__files.extend(file_items)

    def sort_by(self, by: Literal["name", "mtime"]):
        self.__config.sort_by = by
        if self.__save_states:
            self.__config.save(self.__config_file)

        self._list_files()

    def get_selected_file_full_path(self) -> Optional[str]:
        selected = self.get_selected_item()
        if selected:
            full_path = os.path.join(self.get_cur_dir(), selected.name)
            return full_path
        else:
            return None

    # Return the full path of all selected files.
    def get_selected_files(self) -> List[str]:
        return [
            os.path.join(self.get_cur_dir(), file.name)
            for file in self.get_selected_items()
        ]

    def on_exit(self):
        selected = self.get_selected_item(ignore_cancellation=True)
        if selected:
            selected_full_path = os.path.join(self.get_cur_dir(), selected.name)
            self.__config.cur_dir = os.path.dirname(selected_full_path)
            self.__config.selected_file = os.path.basename(selected_full_path)
            if self.__save_states:
                self.__config.save(self.__config_file)

    def open_file(self, full_path: str):
        _, ext = os.path.splitext(full_path)
        if ext.lower() == ".log":
            from utils.menu.logmenu import LogMenu

            LogMenu(files=[full_path]).exec()
        elif ext.lower() in [".zip", ".gz"]:
            subprocess.check_call(["run_script", "r/unzip.py", full_path])
            out_dir = os.path.splitext(full_path)[0]
            self.goto_directory(out_dir)
        else:
            shell_open(full_path)

    def on_enter_pressed(self):
        if self.__select_mode == FileMenu.SELECT_MODE_DIRECTORY:
            self.__selected_files_full_path = [self.get_cur_dir()]
            return super().on_enter_pressed()

        else:
            selected = list(self.get_selected_items())
            if len(selected) == 1:
                full_path = os.path.join(self.get_cur_dir(), selected[0].name)
                if os.path.isdir(full_path):
                    d = os.path.abspath(
                        os.path.join(self.get_cur_dir(), selected[0].name)
                    )
                    self.goto_directory(d)
                    return True
                elif os.path.isfile(full_path):
                    self.__selected_files_full_path = [full_path]
                    if self.__select_mode == FileMenu.SELECT_MODE_FILE:
                        return super().on_enter_pressed()
                    else:
                        self.open_file(full_path)
                        return True
            elif len(selected) > 1 and self.__select_mode == FileMenu.SELECT_MODE_FILE:
                self.__selected_files_full_path = [
                    os.path.join(self.get_cur_dir(), x.name) for x in selected
                ]
                return super().on_enter_pressed()

            else:
                return super().on_enter_pressed()

    def _run_script(self):
        files = self.get_selected_files()
        if len(files) > 0:
            script_dir = os.path.realpath(os.path.dirname(__file__))
            myscripts_path = os.path.abspath(script_dir + "/../../../myscripts.py")
            ret_code = self.call_func_without_curses(
                lambda: subprocess.call(
                    [
                        sys.executable,
                        myscripts_path,
                        "--prompt",
                        "run script on selected files",
                        "--args",
                    ]
                    + files,
                    cwd=self.get_cur_dir(),
                ),
            )
            if ret_code == 0:
                self._refresh_cur_dir()
