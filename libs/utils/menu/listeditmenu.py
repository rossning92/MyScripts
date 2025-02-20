import os
import shutil
from typing import Generic, List, Optional, TypeVar

from utils.jsonutil import load_json, save_json
from utils.menu import Menu

T = TypeVar("T")


class ListEditMenu(Menu, Generic[T]):
    def __init__(
        self,
        items: Optional[List[T]] = None,
        json_file: Optional[str] = None,
        backup_json=False,
        **kwargs
    ):
        self.__json_file = json_file
        self.__backup_json = backup_json

        super().__init__(items=items if items else [], **kwargs)

        self.load_json()

        self.add_command(self.delete_selected_item, hotkey="ctrl+k")

    def load_json(self):
        if self.__json_file is not None:
            self.items[:] = load_json(self.__json_file, default=[])
        if not isinstance(self.items[:], list):
            raise TypeError("JSON data must be a list")

    def delete_selected_item(self):
        index = self.get_selected_index()
        if 0 <= index < len(self.items):
            del self.items[index]
            self.update_screen()
            self.save_json()

    def append_item(self, item: T):
        self.items.append(item)
        self.update_screen()
        self.save_json()

    def clear(self):
        self.items.clear()
        self.update_screen()
        self.save_json()

    def save_json(self):
        if self.__json_file is not None:
            directory = os.path.dirname(self.__json_file)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            if self.__backup_json and os.path.exists(self.__json_file):
                shutil.copy(self.__json_file, self.__json_file + ".bak")
            save_json(self.__json_file, self.items)
