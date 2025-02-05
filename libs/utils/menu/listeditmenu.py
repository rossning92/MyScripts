import os
from typing import Generic, List, Optional, TypeVar

from utils.jsonutil import load_json, save_json
from utils.menu import Menu

T = TypeVar("T")


class ListEditMenu(Menu, Generic[T]):
    def __init__(
        self, items: Optional[List[T]] = None, json_file: Optional[str] = None, **kwargs
    ):
        self.__json_file = json_file

        if json_file is not None:
            items = load_json(json_file, default=[])
        if not isinstance(items, list):
            raise TypeError("JSON data must be a list")

        super().__init__(items=items or [], **kwargs)

        self.add_command(self.delete_selected_item, hotkey="ctrl+k")

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
            os.makedirs(os.path.dirname(self.__json_file), exist_ok=True)
            save_json(self.__json_file, self.items)
