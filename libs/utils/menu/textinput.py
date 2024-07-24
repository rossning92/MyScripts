import datetime
from typing import List, Optional

from _shutil import load_json, save_json

from utils.clip import get_clip

from ..menu import Menu


class TextInput(Menu):
    def __init__(
        self,
        items: Optional[List[str]] = None,
        prompt: str = ">",
        history_list: Optional[List[str]] = None,
        history_file: Optional[str] = None,
        text="",
        show_clipboard: bool = False,
        return_selection_if_empty: bool = False,
    ):
        self.__history_list = history_list
        self.__history_file = history_file
        if self.__history_file:
            self.__history_data = load_json(
                self.__history_file, default={"history": []}
            )
        self.__items = items
        self.__return_selection_if_empty = return_selection_if_empty
        super().__init__(
            prompt=prompt,
            items=([get_clip()] if show_clipboard else [])
            + (
                self.__items
                if self.__items is not None
                else (self.__history_data["history"] if self.__history_file else [])
            ),
            text=text,
        )
        self.add_command(self.__insert_dir_path)
        self.add_command(self.__insert_file_path)
        self.add_command(self.__insert_date, hotkey="alt+d")

    def request_input(self) -> Optional[str]:
        self.exec()
        if self.is_cancelled:
            return None
        else:
            text = self.get_input()
            if self.__history_file:
                if text in self.__history_data["history"]:
                    self.__history_data["history"].remove(text)
                self.__history_data["history"].insert(0, text)
                save_json(self.__history_file, self.__history_data)
            if self.__history_list is not None:
                if text in self.__history_list:
                    self.__history_list.remove(text)
                self.__history_list.insert(0, text)
            if text == "" and self.__return_selection_if_empty:
                return self.get_selected_item()
            else:
                return text

    def __insert_dir_path(self):
        from ..menu.filemgr import FileManager

        dir_path = FileManager(
            goto=self.get_input(),
            prompt="insert dir path",
        ).select_directory()
        if dir_path is not None:
            self.set_input(dir_path)

    def __insert_file_path(self):
        from ..menu.filemgr import FileManager

        file_path = FileManager(
            goto=self.get_input(),
            prompt="insert file path",
        ).select_file()
        if file_path is not None:
            self.set_input(file_path)

    def __insert_date(self):
        self.set_input(datetime.datetime.now().strftime("%Y-%m-%d"))
